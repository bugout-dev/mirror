import requests
import click
import pygit2
import os
import json
import traceback
from typing import Tuple
from pathlib import Path

REMAINING_RATELIMIT_HEADER = 'X-RateLimit-Remaining'

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--crawldir', '-d', default='.', help='Dir for cloned repos.', show_default=True)
@click.option('--stars-expression', '-s', default='>500', help='Stars search condition. ">200" / "=400" / "<300" as example.', show_default=True)
@click.option('--languages', '-ls', nargs=0, required=True)
@click.argument('languages', nargs=-1)
@click.option('--token', '-t', help='Access token for increase rate limit. Read from $github_token if specify.', default='', show_default=True)
@click.option('--amount', '-n', help='Amount of repo.', type=int, default=50, show_default=True)
def clone_repos(crawldir: str, stars_expression: str, languages: Tuple, token: str, amount: int):
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

    if not token:
        if os.environ.get('github_token'):
            token= os.environ.get('github_token')
        else:
            click.echo(f'start with low rate limit')
    
    headers = {'accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {token}'}
    

    resolve_path = Path(crawldir)

    if not os.path.exists(resolve_path):
        os.makedirs(resolve_path)

    with click.progressbar(languages) as bar:        
        for lang in bar:
            try:
                search_expresion = f'stars:{stars_expression}+language:{lang.capitalize()}'

                request_url = f'https://api.github.com/search/repositories?q={search_expresion}&per_page={amount}&page=1'
                search_responce = requests.get(request_url, headers=headers)

                rate_limit_raw = search_responce.headers.get(REMAINING_RATELIMIT_HEADER)

                try:
                    if rate_limit_raw is not None:
                        current_rate_limit = int(rate_limit_raw)
                        if current_rate_limit <= 1:
                            raise ('Rate limit is end.')
                except:
                    raise ('Broken request.')


                data = json.loads(search_responce.text)

                if not data.get("items"):
                    break

                
                print(resolve_path)

                for repo in data["items"]:
                    git_url = repo['git_url']

                    if token:
                        git_url = "".join(("https://",token,'@',git_url.split('//')[1]))

                    print(repo["name"])
                    out_path = resolve_path / lang.capitalize() / repo["name"]
                    if not os.path.exists(out_path):
                        os.makedirs(out_path)
                    else:
                        continue
                    try:
                        pygit2.clone_repository(git_url, out_path)
                    except Exception as err:
                        print(err)
                        
            except:
                traceback.print_exc()

        




if __name__ == "__main__":
    repos()