import httpx
import click
import pygit2
import os
import json
import traceback
from pathlib import Path



@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--output_directory', '-d', default='.', help='Output dir for repos.', show_default=True)
@click.option('--stars_condition', '-s', default='>500', help='Stars search condition.', show_default=True)
@click.option('--languages', '-ls', default='[python]', help='--languages "[o11, o12, o13]" or [o11,o12,o13]', show_default=True)
@click.option('--token', '-t', help='Access token for increase rate limit. Read from $github_token if specify.', default='', show_default=True)
@click.option('--amount', '-n', help='Amount of repo.', default=50, show_default=True)
def repos(output_directory,stars_condition,languages,token, amount):
    token= os.environ.get('github_token', token)

    

    if token == '':
        click.echo(f'Token not found!')
        raise

    
    headers = {'accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {token}'}

    try:
        languages = json.loads(languages)
        
    except ValueError:
        pass
    

    resolve_path = Path(output_directory)

    if not os.path.exists(resolve_path):
        os.makedirs(resolve_path)

    languages = languages[1:-1]  # trim '[' and ']'

    languages_loads = languages.split(',')
    with click.progressbar(languages_loads) as bar:        
        for lang in bar:
            try:
                search_expresion = f'stars:{stars_condition}+language:{lang.capitalize()}'

                request_url = f'https://api.github.com/search/repositories?q={search_expresion}&per_page={amount}&page=1'
                search_responce = httpx.get(request_url, headers=headers)

                data = json.loads(search_responce.text)

                if not data["items"]:
                    break

                 

                for repo in data["items"]:
                    git_url = repo['git_url']
                    resolve_path = Path(output_directory+ f'/{lang.capitalize()}/{repo["name"]}')
                    if not os.path.exists(resolve_path):
                        os.makedirs(resolve_path)
                    pygit2.clone_repository(git_url, resolve_path)
            except:
                traceback.print_exc()

        




if __name__ == "__main__":
    repos()