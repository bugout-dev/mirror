import re
import os
import csv
import sys
import json
import time
import glob
import zipfile
import string
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any

from .utils import flatten_json, get_nearest_value

import requests
import click

from ..settings import GITHUB_TOKEN, module_version
from .utils import write_with_size, read_command_type, request_with_limit
from .data import CommitPublic


DATETIME_HEADER = "Date"


validate_models = {"CommitPublic": CommitPublic}


class MaskStructureError(Exception):
    """Raised when mask missmatch with input json."""

    pass


def dump_date(date, file_index, path):
    file_path = os.path.join(path, f"{file_index}.json")

    with open(file_path, "r", newline="", encoding="utf8") as file:
        data = json.load(file)

    with open(file_path, "w", newline="", encoding="utf8") as file:
        data["crawled_at"] = date
        json.dump(data, file)


def create_file(init_json, file_index, path):
    file_path = os.path.join(path, f"{file_index}.json")

    with open(file_path, "w", encoding="utf8") as file:

        json.dump(init_json, file)


def get_lang(repo):
    """
    Return name of output language folder
    """
    if isinstance(repo["language"], str):
        return repo["language"]
    elif isinstance(repo["language"], list):
        if repo["language"]:
            return repo["language"][0]
    return "Without language"


def validate(data, allowed_data, schema):
    """Take a data structure and apply pydentic model."""
    pydentic_class = validate_models[schema]
    allowed_data.update(pydentic_class(**data).dict())


def create_issues_path(org_path):

    issues_path = os.path.join(org_path, "issues")

    if not os.path.exists(issues_path):
        os.makedirs(issues_path)


def create_dir_meta_if_not_exists(lang_path: str, meta_file: str, lang: str):

    """
    Create nessesary structure
    """

    if not os.path.exists(lang_path):
        os.makedirs(lang_path)

    if not os.path.exists(meta_file):
        with open(meta_file, "w") as meta:
            json.dump(
                {
                    "language": lang,
                    "repos": [],
                    "crawled_at": None,
                    "mirror version": module_version,
                },
                meta,
            )


def commits_parser(github_commits, repo_id, html_url, schema):

    """
    Push commits via validator and add additional fileds.
    return list of json string
    """
    commits = github_commits.json()

    out = list()

    for commit in commits:

        allowed_data = {"repo_id": repo_id, "repo_html_url": html_url}

        if commit:
            validate(flatten_json(commit), allowed_data, schema)

        out.append(allowed_data)

    return commits[0]["sha"], out


def read_repos(repos_dir, file_name, start_id, end_id):
    """
    Read repos from file. Filter repos by given repo id range if specified.
    """
    repos_file_path = os.path.join(repos_dir, file_name)

    # load available repo
    if os.path.isfile(repos_file_path):
        with open(repos_file_path, "r") as repos_file:
            if start_id and end_id:
                return [repo for repo in json.load(repos_file)["data"] if repo["id"]]
            else:
                return json.load(repos_file)["data"]


def create_zip_file(files_dir):
    """
    Create zip inside snippets folder
    """
    with zipfile.ZipFile(
        os.path.join(files_dir, "..", "commits.zip"), "w", zipfile.ZIP_DEFLATED
    ) as zipf:
        for root, dirs, files in os.walk(files_dir):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(
                        os.path.join(root, file), os.path.join(files_dir, "..")
                    ),
                )


def get_repos_files(repos_dir, start_id, end_id):

    """
    Return list of files with repose by given ids range or all files from folder if ids range not set

    In order to make sure that all repositories are covered,
    add 2 additional files from the beginning of the ordered directory list and from the end

    """

    dir_files = os.listdir(repos_dir)

    if not dir_files:
        raise ("Empty repos dir.")

    result_command_type = read_command_type(os.path.join(repos_dir, dir_files[0]))

    if start_id and end_id and result_command_type == "crawl":

        nerest_start_id = get_nearest_value(dir_files, start_id)

        if dir_files.index(f"{nerest_start_id}.json") - 2 <= 0:
            start_index = 0
        else:
            start_file = dir_files.index(f"{nerest_start_id}.json") - 2

        nerest_end_id = get_nearest_value(dir_files, end_id)

        if dir_files.index(f"{nerest_end_id}.json") + 2 >= len(dir_files):
            end_index = -1
        else:
            end_index = dir_files.index(f"{nerest_end_id}.json") + 2

    else:
        return dir_files


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--start-id",
    "-s",
    type=int,
    default=None,
    help="Start repo id for crawl command output.",
)
@click.option(
    "--end-id",
    "-e",
    type=int,
    default=None,
    help="End repo id. You need to specify both parameters start and end id. ",
)
@click.option("--crawldir", "-d", default=".", help='Path to save folder. default="." ')
@click.option("--repos-dir", "-r", help="Directory with repos files.")
@click.option(
    "--schema",
    "-S",
    type=click.Choice(list(validate_models.keys())),
    default="CommitPublic",
    help="Directory with repos files.",
)
@click.option(
    "--token",
    "-t",
    help="Access token for increase rate limit. Read from env $github_token if specify.",
    default=None,
)
@click.option(
    "--min-rate-limit",
    "-l",
    type=int,
    default=10,
    help="Minimum remaining rate limit on API under which the crawl is interrupted",
)
@click.option(
    "no_comment",
    "-N",
    type=bool,
    default=10,
    help="Load issues without comment",
)
def issues(
    start_id: Optional[int],
    end_id: Optional[int],
    crawldir: str,
    repos_dir: str,
    schema: str,
    token: Optional[str],
    min_rate_limit: int,
    no_comment: bool,
):

    """
    Read repos json file and upload all commits for that repos one by one.
    """
    """
    Read repos json file and upload all commits for that repos one by one.
    """

    if not os.path.exists(crawldir):
        os.makedirs(crawldir)

    if not token:
        token = GITHUB_TOKEN

    # rections header
    headers = {"Accept": "application/vnd.github.squirrel-girl-preview+json"}

    if GITHUB_TOKEN is not None:
        headers["Authorization"] = f"token {token}"
    else:
        click.echo(f"start with low rate limit")
        file_index = 1

    files_for_proccessing = get_repos_files(repos_dir, start_id, end_id)

    with click.progressbar(files_for_proccessing, label="Download issues") as bar:

        for repos_file in bar:
            repos = read_repos(repos_dir, repos_file, start_id, end_id)

            if not repos:
                continue

            for repo in repos:
                try:
                    page = 1

                    lang = get_lang(repo)

                    organization_path = os.path.join(crawldir, repo["owner"]["login"])
                    print(organization_path)

                    meta_file = os.path.join(organization_path, "meta.json")

                    create_dir_meta_if_not_exists(organization_path, meta_file, lang)

                    git_url = repo["git_url"]

                    repo_full_name = repo["full_name"]

                    with open(meta_file, "r") as meta:
                        meta_data = json.load(meta)

                    with open(meta_file, "w") as meta:
                        # rewind

                        meta_data["repos"].append(
                            {
                                "name": repo["name"],
                                "full_name": repo["full_name"],
                                "github_repo_url": repo["html_url"],
                                # "commit_hash": commit_hash.decode("utf8"),
                                "license": repo["license"],
                                "fork": repo["fork"],
                                "description": repo["description"],
                                "created_at": repo["created_at"],
                                "updated_at": repo["updated_at"],
                                "pushed_at": repo["pushed_at"],
                                "stargazers_count": repo["stargazers_count"],
                                "watchers_count": repo["stargazers_count"],
                                "forks": repo["stargazers_count"],
                                "open_issues": repo["open_issues"],
                                "private": repo["private"],
                                "owner": {
                                    "type": repo["owner"]["type"],
                                    "html_url": repo["owner"]["html_url"],
                                },
                            }
                        )
                        json.dump(meta_data, meta)
                    repo_path = os.path.join(organization_path, repo["name"])

                    all_isuses = []

                    # # use search endpoint:
                    # init_url = f"https://api.github.com/search/issues?q=repo:{repo_full_name}&per_page=100"

                    # issues_init = request_with_limit(init_url, headers,min_rate_limit).json()

                    all_isuses_loaded = False

                    try:

                        while not all_isuses_loaded:

                            issues = request_with_limit(
                                f"{repo['issues_url'].replace('{/number}','')}?page={page}&per_page=100&state=all&sort=created&direction=asc",
                                headers,
                                min_rate_limit,
                            ).json()

                            all_isuses.extend(issues)

                            page += 1

                            if len(issues) == 0:
                                all_isuses_loaded = True

                    except:
                        pass

                    # ecxtract comments

                    print(f"Issues count: {len(all_isuses)}")

                    for issue in all_isuses:
                        total_comment = 0
                        if not no_comment:

                            page = 1

                            all_comments: List[Dict[Any, Any]] = []

                            init_comments_url = issue["comments_url"]

                            comments_count = issue["comments"]

                            # author_association = issue["author_association"]

                            if comments_count > 0:

                                while len(all_comments) != comments_count:

                                    comments = request_with_limit(
                                        f"{init_comments_url}?per_page=100&page={page}",
                                        headers,
                                        min_rate_limit,
                                    ).json()

                                    if len(comments) == 0:
                                        break

                                    all_comments.extend(comments)

                                    page += 1

                            total_comment += len(all_comments)

                            issues_path = os.path.join(
                                organization_path, repo["name"], "issues"
                            )

                            if not os.path.exists(issues_path):
                                os.makedirs(issues_path)

                            issuse_file = os.path.join(
                                issues_path, f"issue{issue['number']}.json"
                            )

                            with open(issuse_file, "w") as issues_file:

                                json.dump(
                                    {"issue": issue, "comments": all_comments},
                                    issues_file,
                                )
                        else:
                            issues_path = os.path.join(
                                organization_path, repo["name"], "issues"
                            )

                            if not os.path.exists(issues_path):
                                os.makedirs(issues_path)

                            issuse_file = os.path.join(
                                issues_path, f"issue{issue['number']}.json"
                            )

                            with open(issuse_file, "w") as issues_file:

                                json.dump({"issue": issue}, issues_file)

                        print(f"Comment count: {total_comment}")

                except:
                    traceback.print_exc()
                    raise


if __name__ == "__main__":
    issues()
