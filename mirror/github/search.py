import httpx
import re
import click
import os
import csv
import json
import time
from pathlib import Path
import pandas as pd
import string
import traceback






@click.command()
@click.option('--path', '-p', default='.', help='Path to save folder. default="." ')
@click.option('--language', '-l', help='language name search.')
@click.option('--stars', '-st', help='stars amount. 500 or >500 or <500')
@click.option('--format', '-f', type=click.Choice(['csv', 'json'], case_sensitive=False), help='Output file format.')
@click.option('--token', '-t', help='Access token for increase rate limit. Read from $github_token if specify.', default='')
def main(language, stars, path, format, token):

    click.echo(f'format-output: {format}')

    token= os.environ.get('github_token', token)

    if token == '':
        click.echo(f'start with low rate limit')
    

    # create search expression
    init_search_expresion = f'stars:{stars}+language:{language.capitalize()}'

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
    

    # hack for rate limit need rewrite
    
    time_sleep = 3600/10000


    #  make inital request 

    headers = {'accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {token}'}

    search_url = f'https://api.github.com/search/repositories?q={init_search_expresion}&per_page=100'
    click.echo(f' initial request done {search_url}')

    search_responce = httpx.get(search_url, headers=headers)

    time.sleep(time_sleep)

    data = json.loads(search_responce.text)

    # result pagination
    if not data.get('total_count'):
        print('sadassassads')
        click.echo(search_responce.text)
        return


    page_amount = data['total_count']//100

    alredy_parsed = set()

    if data['total_count'] % 100:
        page_amount +=1
    
    global_count = data['total_count']

    # check exists
    resolve_path = Path(path)

    if not os.path.exists(resolve_path):
        os.makedirs(resolve_path)


    # generate file path
    file_path = resolve_path / file_name

    file_modes = 'w+'

    if format == 'csv':
        file_modes = 'a+' 

    file_exist = os.path.isfile(path)
    
    with open(file_path, file_modes, newline='') as output_file:

        if format == 'csv':
            
            # dict normalization for csv propose
            standart_repo = pd.json_normalize(data['items'][0], sep='_')

            csv_headers = standart_repo.keys()
            fieldnames = csv_headers
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            csv_reader = csv.reader(output_file, delimiter=',')

        # already exist file in path
        if file_exist:
            if format == 'csv':

                for row in csv_reader:
                    alredy_parsed.add(row['id'])
            else:

                # read already parsed json
                json_data = json.load(output_file)
                for parsed_repo in json_data['data']:
                    alredy_parsed.add(parsed_repo['id'])
               
        else:
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

            page =0

            try:

                # limitation of search result
                while len(alredy_parsed) != data['total_count'] or page <= 11:

                    # parsing block

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

                    if global_count > 1000:


                        search_expresion = letter+'+' + init_search_expresion
                    
                    else:
                        
                        search_expresion = init_search_expresion
                    

                    # new search
                    
                    request_url = f'https://api.github.com/search/repositories?q={search_expresion}&per_page=100&page={page}'
                    search_responce = httpx.get(request_url, headers=headers)

                    if search_responce.status_code !=200:
                        break

                    data = json.loads(search_responce.text)

                    if not data["items"]:
                        break
                    
                    time.sleep(time_sleep)
                    page += 1
            except:
                traceback.print_exc()

        
        if format != 'csv':
            print(f'Json: {len(json_data["data"])} repo collected.')
            json.dump(json_data, output_file)
        
        

#main('python', '>500', ".", 'json')

if __name__ == "__main__":
    main()