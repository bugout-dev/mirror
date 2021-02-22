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
from typing import Optional

from .utils import flatten_json, get_nearest_value

import requests
import click

from ..settings import GITHUB_TOKEN
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


def validate(data, allowed_data, schema):
    """Take a data structure and apply pydentic model."""
    pydentic_class = validate_models[schema]
    allowed_data.update(pydentic_class(**data).dict())


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
def commits(
    start_id: Optional[int],
    end_id: Optional[int],
    crawldir: str,
    repos_dir: str,
    schema: str,
    token: Optional[str],
    min_rate_limit: int,
):

    """
    Read repos json file and upload all commits for that repos one by one.
    """

    if not os.path.exists(crawldir):
        os.makedirs(crawldir)

    GITHUB_TOKEN = globals()["GITHUB_TOKEN"]

    if token:
        GITHUB_TOKEN = token

    headers = {
        "accept": "application/vnd.github.v3+json",
    }

    if GITHUB_TOKEN is not None:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    else:
        click.echo(f"start with low rate limit")

    file_index = 1

    files_for_proccessing = get_repos_files(repos_dir, start_id, end_id)

    start_block = {"command": "commits", "data": [], "crawled_at": None}

    # 2 output idexing csv and commits
    commits_path = os.path.join(crawldir, "commits")

    csv_out = os.path.join(commits_path, "id_indexes.csv")

    if not os.path.exists(commits_path):
        os.makedirs(commits_path)

    with click.progressbar(files_for_proccessing) as bar, open(
        csv_out, mode="wt", encoding="utf8", newline=""
    ) as output:

        fnames = ["file", "commt_hash", "license", "repo_url", "language"]

        writer = csv.DictWriter(output, fieldnames=fnames)
        writer.writeheader()

        for file_name in bar:

            repos = read_repos(repos_dir, file_name, start_id, end_id)

            if not repos:
                continue

            create_file(start_block, file_index, commits_path)

            for i, repo in enumerate(repos):

                # Get commits
                commits_responce = request_with_limit(repo["commits_url"].replace("{/sha}", ""), headers, min_rate_limit)

                sha, commits = commits_parser(
                    commits_responce, repo["id"], repo["html_url"], schema
                )

                if repo["license"]:
                    license = repo["license"]["spdx_id"]
                else:
                    license = repo["license"]

                # date of creating that commits file
                date = commits_responce.headers.get(DATETIME_HEADER)

                # Indexing
                writer.writerow(
                    {
                        "file": os.path.join("commits", f"{file_index}.json"),
                        "repo_url": repo["html_url"],
                        "commt_hash": sha,
                        "license": license,
                        "language": repo["language"],
                    }
                )

                current_size = write_with_size(commits, file_index, commits_path)

                # Size regulation
                if current_size > 5000000:
                    dump_date(date, file_index, commits_path)
                    file_index += 1
                    create_file(start_block, file_index, commits_path)
                elif i == len(repos) - 1:
                    dump_date(date, file_index, commits_path)
                    file_index += 1
    create_zip_file(commits_path)


if __name__ == "__main__":
    commits()
