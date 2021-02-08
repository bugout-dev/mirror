import requests
import re
import click
import os
import csv
import sys
import json
import time
from utils import write_with_size
from pathlib import Path
import pandas as pd
import string
import traceback



REMAINING_RATELIMIT_HEADER = 'X-RateLimit-Remaining'



def request_with_limit(repo, headers, min_rate_limit):
    try:
        while True:

            response = requests.get(repo['commits_url'].replace('{/sha}',''), headers=headers)
        
            rate_limit_raw = response.headers.get(REMAINING_RATELIMIT_HEADER)

            if rate_limit_raw is not None:
                current_rate_limit = int(rate_limit_raw)
                if current_rate_limit <= min_rate_limit:
                    
                    print('Rate limit is end. Awaiting 1 minute.')
                    time.sleep(60)
                else:
                    break
        return response
    except:
        raise ('Broken request.')

@click.command()
@click.option('--crawldir', '-d', default='.', help='Path to save folder. default="." ')

@click.option('--repos-file', '-f', help='Input repos file.')

@click.option('--token', '-t', help='Access token for increase rate limit. Read from env $github_token if specify.', default=None)

@click.option('--min-rate-limit', '-l', type=int, default=30, help='Minimum remaining rate limit on API under which the crawl is interrupted')
def commits(crawldir: str, repos_file: str, token: str, min_rate_limit: int):

    """
    Read repos json file and upload all commits for that repos one by one.
    """
    if not token:
        if os.environ.get('github_token'):
            token= os.environ.get('github_token')
        else:
            click.echo(f'start with low rate limit')
    
    source_file_path = Path(repos_file)
    file_exist = source_file_path.is_file()
    
    # load available repo
    if file_exist:
        with open(source_file_path, 'r') as repos_file:
            repos_data = json.loads(repos_file.read())
    else:
        return
    
    file_template = {
        'source_file_name': None,
        'data': []
    }
    
    start_block = '{'+ f'"source_file_name": "{source_file_path.name}", "data": ['

    end_block = ']}'

    content_name = "commit"

    ext = 'json'

    resolve_path = Path(crawldir)

    if not os.path.exists(resolve_path):
        os.makedirs(resolve_path)

    

    headers = {'accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {token}'}

    file_index = 1

    write_with_size(start_block, content_name, file_index, resolve_path, ext)

    repo_amount = len(repos_data['data'])
    
    with click.progressbar(repos_data['data']) as bar:
        for i,repo in enumerate(bar):

            

            #request commits
            while True:
                commits_responce = request_with_limit(repo, headers, min_rate_limit)

            commits_data = commits_responce.json()

            repo_dump = json.dumps({repo['id']:commits_data})

            current_size = write_with_size(repo_dump, content_name, file_index, resolve_path, ext)

            if current_size >5000000:
                
                write_with_size(end_block, content_name, file_index, resolve_path, ext)
                file_index += 1
                write_with_size(start_block, content_name, file_index, resolve_path, ext)
            else:
                if i != repo_amount - 1:
                    write_with_size(',', content_name, file_index, resolve_path, ext)
    write_with_size(end_block, content_name, file_index, resolve_path, ext) 


if __name__ == "__main__":
    commits()