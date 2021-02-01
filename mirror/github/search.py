import requests
import click
import os
import csv
import json
import time
from pathlib import Path
import pandas as pd
import string
import traceback
from typing import Optional

from ..settings import GITHUB_TOKEN


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


def request_with_limit(url, headers, min_rate_limit):
    try:
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
    except:
        raise ('Broken request.')




REMAINING_RATELIMIT_HEADER = 'X-RateLimit-Remaining'

@click.command()
@click.option('--crawldir', '-d', default='./', help='Path to save folder.', show_default=True)

@click.option('--language', '-l', help='Language name for search.')

@click.option('--stars_expression', '-st', help='Stars amount. "500" or ">500" or "<500"')

@click.option('--format', '-f', type=click.Choice(['csv', 'json'], case_sensitive=False), help='Output file format.', default='json', show_default=True)

@click.option('--token', '-t', help='Access token for increase rate limit. Read from env $GITHUB_TOKEN if specify.', default=None, show_default=True)

@click.option('--min-rate-limit', '-r', type=int, default=30, help='Minimum remaining rate limit on API under which the crawl is interrupted')
def popular_repos(language: str, stars_expression: str, crawldir: str, format: str, token: Optional[str], min_rate_limit: int):

    """
    Crawl via search api.
    Search api have limitation 1000 results per search quary.
    For extract more results from search for each request we adding letters of the alphabet to the query parameter.

    """

    click.echo(f'format-output: {format}')

    if GITHUB_TOKEN is None:
        click.echo(f'start with low rate limit')

    # create search expression
    init_search_expresion = f'stars:{stars_expression}+language:{language.capitalize()}'

    # generate file name maybe need just search_python
    addition_naming = ''
    query_params = init_search_expresion.split('+')
    for specify_string in query_params:
        addition_naming += '_' + specify_string.replace(':','_').replace('<','less_then_').replace('>','more_then_')

    #select ext
    if format == 'csv':
        file_name = f'repo_search_{addition_naming}.csv'
    else:
        file_name = f'repo_search_{addition_naming}.json'


    #  make inital request 

    headers = {'accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {GITHUB_TOKEN}'}

    search_url = f'https://api.github.com/search/repositories?q={init_search_expresion}&per_page=100'
   
    search_response = request_with_limit(search_url, headers, min_rate_limit)

    click.echo(f' initial request done {search_url}')

    data = json.loads(search_response.text)

    # result pagination
    if not data.get('total_count'):
        click.echo(search_response.text)
        return

    # etract total count github limit is 10 page of search result
    page_amount = data['total_count']//100

    alredy_parsed = set()

    if data['total_count'] % 100:
        page_amount +=1
    
    global_count = data['total_count']

    # check exists
    resolve_path = Path(crawldir)

    if not os.path.exists(resolve_path):
        os.makedirs(resolve_path)

    # generate file path
    file_path = resolve_path / file_name

    file_exist = os.path.isfile(file_path)

    file_modes = 'w+'


    with open(file_path, file_modes, newline='') as output_file:

        

        if format == 'csv':
            
            # dict normalization for csv propose
            standart_repo = pd.json_normalize(data['items'][0], sep='_')

            csv_headers = standart_repo.keys()
            fieldnames = csv_headers
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            

        if format == 'csv':
            writer.writeheader()
        else:
            # simple template object
            json_data = { 
                'data':[]
            }
        
        # Put letter by letter to search query
        #
        
        for letter in list(string.ascii_lowercase):

            page = 1

            try:

                # limitation of search result
                while len(alredy_parsed) <= global_count and page <= 10:


                    
                    if global_count > 1000:


                        search_expresion = letter+'+' + init_search_expresion
                    
                    else:
                        
                        search_expresion = init_search_expresion
                    

                    # parsing block
                    request_url = f'https://api.github.com/search/repositories?q={search_expresion}&per_page=100&page={page}'

                    search_response = request_with_limit(search_url, headers, min_rate_limit)

                    data = json.loads(search_response.text)


                    if not data.get('items'):
                        break

                    repos = data['items']


                    for repo in repos:

                        if repo['id'] not in alredy_parsed:

                            if format == 'csv':

                                repo_normalization = pd.json_normalize(repo, sep='_')
                                
                                writer.writerow(repo_normalization)
                            else:
                                json_data['data'].append(repo)
                        else:
                            continue

                        alredy_parsed.add(repo['id'])
                    
                    page += 1
            except:
                traceback.print_exc()

        
        if format != 'csv':
            print(f'Json: {len(json_data["data"])} repo collected.')
            json.dump(json_data, output_file)
        
if __name__ == "__main__":
    popular_repos()