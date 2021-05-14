"""
Popular repositories search engine.
"""
import os
import json
import string
import traceback
import urllib.parse
from typing import Optional

import click

from .. import settings
from .utils import forward_languages_config, request_with_limit


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


def encode_query(stars_expression, language):
    stars_encoding = str(urllib.parse.quote(f"stars:{stars_expression}"))
    lang_encoding = str(urllib.parse.quote(f"language:{language.capitalize()}"))
    return f"{stars_encoding}+{lang_encoding}"


def get_total_count(search_query, headers, min_rate_limit):
    search_url = (
        f"https://api.github.com/search/repositories?q={search_query}&per_page=100"
    )

    search_response = request_with_limit(search_url, headers, min_rate_limit)

    click.echo(f" initial request done {search_url}")

    data = json.loads(search_response.text)

    # result pagination
    return data.get("total_count")


def write_repos(data, alredy_parsed, date, files_counter, path, language, search_query):

    json_data = {"data": []}

    repos = data["items"]

    for repo in repos:

        if repo["id"] not in alredy_parsed:

            json_data["data"].append(repo)
        else:
            continue

        alredy_parsed.add(repo["id"])

    json_data["command"] = "search"

    json_data["crawled_at"] = date
    json_data["language"] = language
    json_data["search_query"] = search_query

    file_path = os.path.join(path, f"{files_counter}.json")

    with open(file_path, "w+", newline="") as output_file:
        json.dump(json_data, output_file)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--crawldir", "-d", default="./", help="Path to save folder.", show_default=True
)
@click.option(
    "--stars_expression", "-s", help='Stars amount. "500" or ">500" or "<500"'
)
@click.option(
    "--token",
    "-t",
    help="Access token for increase rate limit. Read from env $GITHUB_TOKEN if specify.",
    default=None,
    show_default=True,
)
@click.option(
    "--languages",
    "-L",
    nargs=0,
    help="Specify languages for extraction. Mirror ignoring that parametr if languages file is specified.",
)
@click.argument("languages", nargs=-1)
@click.option(
    "--min-rate-limit",
    "-l",
    type=int,
    default=10,
    help="Minimum remaining rate limit on API under which the crawl is interrupted",
)
@click.option(
    "--languages-file", "-f", help="Path to json file with languages for extracting."
)
def popular_repos(
    languages: tuple,
    stars_expression: str,
    crawldir: str,
    token: Optional[str],
    min_rate_limit: int,
    languages_file: str,
):
    """
    Crawl via search api.
    Search api have limitation 1000 results per search quary.
    For extract more results from search for each request we adding letters of the alphabet to the query parameter.

    For languages file have next format. Languages name must match with the github.
    {"languages":["lang1",
                  "lang2",
                  ......
                  "langN"]
    }

    """

    if not token:
        token = settings.GITHUB_TOKEN

    headers = {
        "accept": "application/vnd.github.v3+json",
    }

    if settings.GITHUB_TOKEN is not None:
        headers["Authorization"] = f"token {token}"
    else:
        click.echo(f"start with low rate limit")

    if not os.path.exists(crawldir):
        os.makedirs(crawldir)

    if languages_file:
        try:
            with open(languages_file, "r", encoding="utf8") as langs:
                languages = json.load(langs)

            forward_languages_config(languages_file, crawldir)

        except Exception as err:
            traceback.print_exc()
            print(f"Can't read langiages file. {err}")

    files_counter = 0

    for language in languages:

        # create search expression
        init_search_query = encode_query(stars_expression, language)

        total_count = get_total_count(init_search_query, headers, min_rate_limit)
        if not total_count:
            continue

        alredy_parsed: set = set()

        # etract total count github limit is 10 page of search result
        page_amount = total_count // 100

        if total_count % 100 and total_count < 1000:
            page_amount += 1

        if not os.path.exists(crawldir):
            os.makedirs(crawldir)

        for letter in list(string.ascii_lowercase):

            page = 1

            try:

                # limitation of search result
                while len(alredy_parsed) <= total_count and page <= 10:

                    if total_count > 1000:
                        search_expresion = letter + "+" + init_search_query
                    else:
                        search_expresion = init_search_query

                    # parsing block

                    search_url = f"https://api.github.com/search/repositories?q={search_expresion}&per_page=100&page={page}"

                    search_response = request_with_limit(
                        search_url, headers, min_rate_limit
                    )

                    data = json.loads(search_response.text)

                    if not data.get("items"):
                        break

                    files_counter += 1

                    write_repos(
                        data,
                        alredy_parsed,
                        search_response.headers.get(settings.DATETIME_HEADER),
                        files_counter,
                        crawldir,
                        language,
                        search_url,
                    )

                    page += 1
            except KeyboardInterrupt:
                raise KeyboardInterrupt("CTRL+C")
            except:
                traceback.print_exc()
                raise

            if total_count <= 1000:
                break


if __name__ == "__main__":
    popular_repos()
