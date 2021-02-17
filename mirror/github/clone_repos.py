import os
import json
import time
import traceback
import subprocess
import urllib.parse
from typing import Tuple, Optional
from pathlib import Path


import click
import requests

from ..settings import GITHUB_TOKEN, module_version
from .utils import get_nearest_value, read_command_type, forward_languages_config

REMAINING_RATELIMIT_HEADER = "X-RateLimit-Remaining"
DATETIME_HEADER = "Date"


class CommandNotExistError(Exception):
    """Raised when coomand is not exist."""

    pass


def request_with_limit(url, headers, min_rate_limit):

    while True:

        response = requests.get(url, headers=headers)

        rate_limit_raw = response.headers.get(REMAINING_RATELIMIT_HEADER)

        if rate_limit_raw is not None:
            current_rate_limit = int(rate_limit_raw)
            if current_rate_limit <= min_rate_limit:

                print("Rate limit is end. Awaiting 1 minute.")
                time.sleep(60)
            else:
                break
    return response


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


def check_command(name):
    """
    Check whether `name` is on PATH and marked as executable.
    """

    # from whichcraft import which
    from shutil import which

    return which(name) is not None


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


def read_repos(repos_dir, file_name, start_id, end_id):
    """
    Read repos from file. Filter repos by given repo id range if specified.
    """
    repos_file_path = os.path.join(repos_dir, file_name)

    # load available repo
    if os.path.isfile(repos_file_path):
        with open(repos_file_path, "r") as repos_file:
            if start_id and end_id:
                return [
                    repo for repo in json.loads(repos_file.read())["data"] if repo["id"]
                ]
            else:
                return json.loads(repos_file.read())["data"]


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


def clone_repository(git_url, out_path):
    cmd = f"git clone {git_url}"
    pipe = subprocess.Popen(cmd, shell=True, cwd=out_path)
    pipe.wait()


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
@click.option(
    "--crawldir", "-d", default=None, help="Dir for cloned repos.", show_default=True
)
@click.option(
    "--repos-dir",
    "-r",
    default=None,
    help="Dir with crawled repos metadata.",
    show_default=True,
)
@click.option(
    "--token",
    "-t",
    help="Access token for increase rate limit. Read from $GITHUB_TOKEN if specify.",
    default="",
    show_default=True,
)
def clone_repos(
    start_id: Optional[int],
    end_id: Optional[int],
    crawldir: str,
    repos_dir: str,
    token: str,
):
    """
    Clone repos from search api to output dir.
    Be careful check of upload size not provide
    """

    if not check_command("git"):
        raise CommandNotExistError("Git not found.")

    if not token:
        GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    else:
        GITHUB_TOKEN = token

    if os.path.exists(os.path.join(repos_dir, "languages_config.json")):
        forward_languages_config(
            os.path.join(repos_dir, "languages_config.json"), repos_dir
        )

    if not os.path.exists(crawldir):
        os.makedirs(crawldir)

    headers = {
        "accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}",
    }

    # read metadata
    files_for_proccessing = get_repos_files(repos_dir, start_id, end_id)

    with click.progressbar(files_for_proccessing, label="Download repos") as bar:
        for repos_file in bar:

            repos = read_repos(repos_dir, repos_file, start_id, end_id)

            if not repos:
                continue

            for repo in repos:
                try:
                    lang = get_lang(repo)

                    lang_path = os.path.join(crawldir, lang)

                    meta_file = os.path.join(lang_path, "meta.json")

                    create_dir_meta_if_not_exists(lang_path, meta_file, lang)

                    git_url = repo["git_url"]

                    # if GITHUB_TOKEN:
                    #     git_url = "".join(("https://",GITHUB_TOKEN,'@',git_url.split('//')[1]))

                    clone_repository(git_url, lang_path)

                    # commits_response = request_with_limit(repo["commits_url"].replace('{/sha}',''), headers, 5).json()[0]
                    commit_hash = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        stdout=subprocess.PIPE,
                        swd=os.path.join(lang_path, repo["name"]),
                    ).stdout

                    with open(meta_file, "r+") as meta:
                        meta_data = json.load(meta)

                        meta_data["repos"].append(
                            {
                                "name": repo["name"],
                                "full_name": repo["full_name"],
                                "github_repo_url": repo["html_url"],
                                "commit_hash": commit_hash.decode("utf8"),
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

                except KeyboardInterrupt:
                    raise KeyboardInterrupt("CTRL+C")

                except:
                    traceback.print_exc()

    #         with open(os.path.join(crawldir, lang.capitalize(), "meta.json"), 'w') as meta_file:
    #             meta_data["crawled_at"] = search_response.headers.get(DATETIME_HEADER)
    #             json.dump(meta_data, meta_file)
    # with open(os.path.join(crawldir, "languages_config.json"), 'w') as save_config:
    #     json.dump(langs_conf, save_config)


if __name__ == "__main__":
    clone_repos()
