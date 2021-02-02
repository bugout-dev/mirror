import requests
import click
import os
import csv
import json
import time
from pathlib import Path
import urllib.parse
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

@click.option('--token', '-t', help='Access token for increase rate limit. Read from env $GITHUB_TOKEN if specify.', default=None, show_default=True)

@click.option('--min-rate-limit', '-r', type=int, default=30, help='Minimum remaining rate limit on API under which the crawl is interrupted')

@click.option('--languages-file', '-f', help='Path to json file with languages for extracting.')

def popular_repos(language: str, stars_expression: str, crawldir: str, token: Optional[str], min_rate_limit: int, languages_file: str):

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

    if GITHUB_TOKEN is None:
        click.echo(f'start with low rate limit')
    
    if languages_file:
        try:
            langs_file = Path(languages_file)
            with langs_file.open('r', encoding='utf8') as langs:
                langs_conf = json.load(langs)
            languages = langs_conf["languages"]
        except Exception as err:
            print("Can't read langiages file. {err}")
    else:
        languages= [language]

    for language in languages:

        # create search expression
        stars_encoding = urllib.parse.urlencode(f"stars:{stars_expression}")
        lang_encoding = urllib.parse.urlencode(f"language:{language.capitalize()}")
        init_search_expresion = f'{stars_encoding}+{lang_encoding}'

        # generate file name maybe need just search_python
        addition_naming = ''
        query_params = init_search_expresion.split('+')
        for specify_string in query_params:
            addition_naming += '_' + specify_string.replace(':','_').replace('<','less_then_').replace('>','more_then_')


        file_name = f'repo_search_{addition_naming}.json'


        #  make inital request 

        headers = {'accept': 'application/vnd.github.v3+json',
                    'Authorization': f'token {GITHUB_TOKEN}'}


        search_url = f'https://api.github.com/search/repositories?q={init_search_expresion}&per_page=100'

        search_response = request_with_limit(search_url, headers, min_rate_limit, params)

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
                        params = [('q',search_expresion),('per_page',100),('page',page)]

                        search_url = f'https://api.github.com/search/repositories?q={search_expresion}&per_page=100&page={page}'

                        search_response = request_with_limit(search_url, headers, min_rate_limit)

                        data = json.loads(search_response.text)


                        if not data.get('items'):
                            break

                        repos = data['items']


                        for repo in repos:

                            if repo['id'] not in alredy_parsed:

                                json_data['data'].append(repo)
                            else:
                                continue

                            alredy_parsed.add(repo['id'])
                        
                        page += 1
                except:
                    traceback.print_exc()

            
            
            print(f'Json: {len(json_data["data"])} {language} repo collected.')
            json.dump(json_data, output_file)
        
if __name__ == "__main__":
    popular_repos()