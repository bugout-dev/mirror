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

from ..settings import GITHUB_TOKEN, module_version

REMAINING_RATELIMIT_HEADER = 'X-RateLimit-Remaining'
DATETIME_HEADER = 'Date'

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
@click.option('--crawldir', '-d', default=None, help='Dir for cloned repos.', show_default=True)
@click.option('--stars-expression', '-s', default='>500', help='Stars search condition. ">200" / "=400" / "<300" as example.', show_default=True)
@click.option('--languages', '-L', nargs=0, help="Specify languages for extraction. Mirror ignoring that parametr if languages file is specified.")
@click.argument('languages', nargs=-1)
@click.option('--token', '-t', help='Access token for increase rate limit. Read from $GITHUB_TOKEN if specify.', default='', show_default=True)
@click.option('--amount', '-n', help='Amount of repo per language.', type=int, default=50, show_default=True)
@click.option('--languages-file', '-f', help='Path to json file with languages for extracting. If not specified read from enviroment.')


def clone_repos(crawldir: str, stars_expression: str, languages: Tuple, token: str, amount: int, languages_file: str):
    """
    Clone repos from search api to output dir.
    Be careful check of upload size not provide
    """
    if not token:
        GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    else:
        GITHUB_TOKEN = token


    if not os.path.exists(crawldir):
        os.makedirs(crawldir)
    
    if languages_file:
        # read languages file
        try:
            with open(languages_file, 'r', encoding='utf8') as langs:
                langs_conf = json.load(langs)
            
            languages = langs_conf.keys()
        except Exception as err:
            raise ConfigReadError(f"Can't read langiages file. {err}")
    
    headers = {'accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {GITHUB_TOKEN}'}

    with click.progressbar(languages, label='Download repos') as bar:        
        for lang in bar:
            
            try:
                    
                query_search_expresion = encode_query(stars_expression, lang)

                meta_data = {
                    "language": lang,
                    "query": query_search_expresion,
                    "amount":amount,
                    "repos": [],
                    "crawled_at": None,
                    "mirror version": module_version
                }

                request_url = f'https://api.github.com/search/repositories?q={query_search_expresion}&per_page={amount}&page=1'

                search_response = request_with_limit(request_url, headers, 5)

                data = json.loads(search_response.text)

                if not data.get("items"):
                    break

                for repo in data["items"]:
                    git_url = repo['git_url']

                    if GITHUB_TOKEN:
                        git_url = "".join(("https://",GITHUB_TOKEN,'@',git_url.split('//')[1]))

                    #print(f"Repository name: {repo['name']}")
                    out_path = os.path.join(crawldir, lang.capitalize(), repo["name"])

                    if not os.path.exists(out_path):
                        os.makedirs(out_path)
                    else:
                        continue

                    pygit2.clone_repository(git_url, out_path)

                    commits_response = request_with_limit(repo["commits_url"].replace('{/sha}',''), headers, 5).json()[0]

                    meta_data["repos"].append({
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "github_repo_url": repo["html_url"],
                        "commit_hash":commits_response["sha"],
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
                        }
                        
                    })
            
            except KeyboardInterrupt:
                raise KeyboardInterrupt('CTRL+C')
                        
            except:
                traceback.print_exc()

            with open(os.path.join(crawldir, lang.capitalize(), "meta.json"), 'w') as meta_file:
                meta_data["crawled_at"] = search_response.headers.get(DATETIME_HEADER)
                json.dump(meta_data, meta_file)
    with open(os.path.join(crawldir, "languages_config.json"), 'w') as save_config:
        json.dump(langs_conf, save_config)

        




if __name__ == "__main__":
    clone_repos()