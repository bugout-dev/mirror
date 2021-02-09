import os
import json
import time
import traceback
import urllib.parse
from typing import Tuple
from pathlib import Path


import click
import pygit2 # type: ignore
import requests

from ..settings import GITHUB_TOKEN

REMAINING_RATELIMIT_HEADER = 'X-RateLimit-Remaining'

class ConfigReadError(Exception):
    """Raised when the input value is too small"""
    pass

def request_with_limit(url, headers, min_rate_limit):

    while True:

        response = requests.get(url, headers=headers)
    
        rate_limit_raw = response.headers.get(REMAINING_RATELIMIT_HEADER)

        if rate_limit_raw is not None:
            current_rate_limit = int(rate_limit_raw)
            if current_rate_limit <= min_rate_limit:
                
                print('Rate limit is end. Awaiting 1 minute.')
                time.sleep(60)
            else:
                break
    return response


def encode_query(stars_expression, language):
    stars_encoding = str(urllib.parse.unquote_plus(f"stars:{stars_expression}"))
    lang_encoding = str(urllib.parse.unquote_plus(f"language:{language.capitalize()}"))
    return f'{stars_encoding}+{lang_encoding}'


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--crawldir', '-d', default='.', help='Dir for cloned repos.', show_default=True)
@click.option('--stars-expression', '-s', default='>500', help='Stars search condition. ">200" / "=400" / "<300" as example.', show_default=True)
@click.option('--languages', '-L', nargs=0, help="Specify languages for extraction. Mirror ignoring that parametr if languages file is specified.")
@click.argument('languages', nargs=-1)
@click.option('--token', '-t', help='Access token for increase rate limit. Read from $GITHUB_TOKEN if specify.', default='', show_default=True)
@click.option('--amount', '-n', help='Amount of repo.', type=int, default=50, show_default=True)
@click.option('--languages-file', '-f', help='Path to json file with languages for extracting.')


def clone_repos(crawldir: str, stars_expression: str, languages: Tuple, token: str, amount: int, languages_file: str):
    """
    Clone repos from search api to output dir.
    Be careful check of upload size not provide

    output structure:
    - crawldir
      - language 1
        - repo 1
        - repo 2
        ...
      - language 2
        - repo 1
        - repo 2
        ...
      ...


    """

    if GITHUB_TOKEN is None:
        click.echo(f'start with low rate limit')
    
    headers = {'accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {GITHUB_TOKEN}'}

    if not os.path.exists(crawldir):
        os.makedirs(crawldir)

    if languages_file:
        try:

            with open(languages_file, 'r', encoding='utf8') as langs:
                langs_conf = json.load(langs)
            
            languages = langs_conf.keys()
        except Exception as err:
            raise ConfigReadError(f"Can't read langiages file. {err}")

    with click.progressbar(languages) as bar:        
        for lang in bar:

            try:
                    
                query_search_expresion = encode_query(stars_expression, lang)

                request_url = f'https://api.github.com/search/repositories?q={query_search_expresion}&per_page={amount}&page=1'

                search_response = request_with_limit(request_url, headers, 5)

                data = json.loads(search_response.text)

                if not data.get("items"):
                    break

                for repo in data["items"]:
                    git_url = repo['git_url']

                    if GITHUB_TOKEN:
                        git_url = "".join(("https://",GITHUB_TOKEN,'@',git_url.split('//')[1]))

                    print(f"Repository name: {repo['name']}")
                    out_path = os.path.join(crawldir, lang.capitalize(), repo["name"])

                    if not os.path.exists(out_path):
                        os.makedirs(out_path)
                    else:
                        continue

                    pygit2.clone_repository(git_url, out_path)
            
            except KeyboardInterrupt:
                raise KeyboardInterrupt('CTRL+C')
                        
            except:
                traceback.print_exc()

        




if __name__ == "__main__":
    clone_repos()