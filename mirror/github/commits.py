import requests
import re
import click
import os
import csv
import sys
import json
import time
from pathlib import Path
import pandas as pd
import string
import traceback




def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


def write_with_size(string,file_index, path):
    """
    Return current size after writing
    """
    file_path = path / f'commits_{file_index}.json'
    with open(file_path, 'a', newline='') as file:
        file.write(string)
        size_of_file = file.tell()
    return size_of_file


@click.command()
@click.option('--path', '-p', default='.', help='Path to save folder. default="." ')
@click.option('--file', '-f', help='Input repos file.')
@click.option('--token', '-t', help='Access token for increase rate limit. Read from $github_token if specify.', default='')
def main(path: str, file: str, token: str):
    token= os.environ.get('github_token', token)

    if token == '':
        click.echo(f'start with low rate limit')
    
    print(os.listdir('./'))

    source_file_path = Path(file)
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

    

    resolve_path = Path(path)

    if not os.path.exists(resolve_path):
        os.makedirs(resolve_path)

    

    headers = {'accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {token}'}

    file_index = 1

    write_with_size(start_block,file_index,resolve_path)

    with click.progressbar(repos_data['data']) as bar:
        for repo in bar:

            #request commits
            try:

                commits_responce = requests.get(repo['commits_url'].replace('{/sha}',''), headers=headers)
            except:
                continue

            commit_data = json.load(commits_responce)

            repo_dump = json.dumps({repo['id']:commit_data})

            current_size = write_with_size(repo_dump, file_index, resolve_path)

            if current_size >5000000:
                
                write_with_size(end_block, file_index, resolve_path)
                file_index += 1
                write_with_size(start_block, file_index, resolve_path)
            else:
                write_with_size(',', file_index, resolve_path)
    write_with_size(end_block, file_index, resolve_path) 


if __name__ == "__main__":
    main()