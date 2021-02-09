
import re
import os
import csv
import sys
import json
import time
import click
import string
import requests
import traceback
import pandas as pd
from pathlib import Path
from typing import Optional

from utils import write_with_size


REMAINING_RATELIMIT_HEADER = 'X-RateLimit-Remaining'

DATETIME_HEADER = 'Date'


def get_nearest_value(iterable, value):
    return min(iterable, key=lambda x: abs(int(x.split('.')[0]) - value))


def read_repos(repos_dir, file_name, start_id, end_id):
    repos_file_path = os.path.join(repos_dir, file_name)
    
    # load available repo
    if os.path.isfile(repos_file_path):
        with open(repos_file_path, 'r') as repos_file:
            if start_id and end_id:
                return [repo for repo in json.loads(repos_file.read())['data'] if repo["id"]]
            else:
                return json.loads(repos_file.read())['data']



def request_with_limit(repo, headers, min_rate_limit):

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


def read_command_type(path):
    """
    Return type of command wich generated repos inside repos folder
    """
    with open(path, 'r', encoding='utf8') as first_file:
        data = json.loads(first_file.read)
    return data["command"]


def get_repos_files(repos_dir, start_id, end_id):

    """
    Return list of files with repose by given ids range or all files from folder if ids range not set

    In order to make sure that all repositories are covered,
    add 2 additional files from the beginning of the ordered directory list and from the end 

    """

    dir_files = os.listdir(repos_dir)

    if not list_dir:
        raise('Empty repos dir.')

    result_command_type = read_command_type(os.path.join(craw, dir_files[0]))

    if start_id and end_id and  result_command_type == "crawl":

        nerest_start_id = get_nearest_value(start_id)

        if dir_files.index(f"{nerest_start_id}.json")-2 <= 0:
            start_index = 0
        else:
            start_file = dir_files.index(f"{nerest_start_id}.json")-2
        
        
        nerest_end_id = get_nearest_value(end_id)

        if dir_files.index(f"{nerest_end_id}.json")+2  >= len(dir_files):
            end_index = -1
        else:
            end_index = dir_files.index(f"{nerest_end_id}.json")+2
    
    else:
        return list_dir


@click.command()

@click.option('--start-id', '-s', type=int, default=None, help='Start repo id for crawl command output.')

@click.option('--end-id', '-m', type=int, default=None, help='End repo id. You need to specify both parameters start and end id. ')

@click.option('--crawldir', '-d', default='.', help='Path to save folder. default="." ')

@click.option('--repos-dir', '-r', help='Directory with repos files.')

@click.option('--token', '-t', help='Access token for increase rate limit. Read from env $github_token if specify.', default=None)

@click.option('--min-rate-limit', '-l', type=int, default=30, help='Minimum remaining rate limit on API under which the crawl is interrupted')

def commits(start-id: Optional[int], end-id: Optional[int], crawldir: str, repos_dir: str, token: str, min_rate_limit: int):

    """
    Read repos json file and upload all commits for that repos one by one.
    """
    
    if not os.path.exists(crawldir):
        os.makedirs(crawldir)


    if not token:
        if os.environ.get('github_token'):
            token= os.environ.get('github_token')
        else:
            click.echo(f'start with low rate limit')
    
    headers = {'accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {token}'}

    file_index = 1

    files_for_proccessing = get_repos_files(repos_dir, start_id, end_id)

    start_block = '{'+ f'"command": "commits", "data": ['

    
    # 2 output idexing csv and commits

    csv_out = os.join.path(crawldir, 'id_indexes.csv')

    commits_out = os.join.path(crawldir, "commits")
    

    with click.progressbar(files_for_proccessing) as bar, open(csv_out, mode='wt', encoding='utf8', newline='') as output:

        fnames = ['file', 'repo_id']

        writer = csv.DictWriter(output, fieldnames=fnames)
        writer.writeheader()

        for i,file_name in enumerate(bar):

            repos = read_repos(repos_dir, file_name, start_id, end_id)

            if not repos:
                continue

            write_with_size(start_block, content_name, file_index, commits_out, ext)
    
            for repo in repos:

                # Get commits
                commits_responce = request_with_limit(repo, headers, min_rate_limit)

                commits_data = commits_responce.json()

                repo_dump = json.dumps({repo['id']:commits_data})


                # date of creating that commits file
                date = commits_responce.headers.get(DATETIME_HEADER)

                # Indexing
                writer.writerow({'file' : os.path.join(commits_out, f"{file_index}.json"),
                                 'repo_id': repo['id'])
                
                current_size = write_with_size(repo_dump, file_index, commits_out)

                # Size regulation
                if current_size >5000000:
                    
                    write_with_size(f'], "crawled_at": "{date}"', file_index, commits_out)
                    file_index += 1
                    write_with_size(start_block, file_index, commits_out)
                else:
                    if i != len(repos) - 1:
                        write_with_size(',', file_index, commits_out)

            write_with_size(f'], "crawled_at": "{date}"', file_index, commits_out)
            file_index += 1


if __name__ == "__main__":
    commits()