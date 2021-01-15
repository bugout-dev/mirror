import csv
import json
import os
import click
from pathlib import Path
import pandas as pd





@click.command()
@click.option('--json-files-folder', '-p', default='.', help='folders with repo/commits. default="." ')
@click.option('--output-csv', '-f', help='Output csv normilize file.')
@click.option('--command', '-t', help='specify wich type of content need extract.')
def json_files_to_csv(command: str, path_input_folder: str, path_output_csv: str):
    """
    Generate one csv file from json files

    """

    inputs_path = Path(path_input_folder)

    output_file = Path(path_output_csv)
    print(inputs_path.is_dir(),output_file.exists())

    if not inputs_path.is_dir():
        return

    # if output_file.exists():
    #     return

    if command=='commits':

        json_list = [file for file in os.listdir(inputs_path) if 'commits' in file]
        
        # init csv 
        read_file = inputs_path /json_list[0]

        with open(read_file, 'r') as income, open(output_file, 'a', newline='') as csv_out:
            json_data = json.loads(income.read())['data']
            print(json_data[0].keys())
            first_repo = list(json_data[0].keys())[0]
            commit = json_data[0][first_repo][0]


            # generate commit header
            
            standart_commit = pd.json_normalize(commit, sep='_')

            csv_headers = standart_commit.keys()
            fieldnames = csv_headers
            print(fieldnames)
            writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
            writer.writeheader()

        
        
        print(len(json_list))
        # list of files
        for json_file in json_list:
            read_file = inputs_path / json_file

            with open(read_file, 'r') as income:
                json_data = json.loads(income.read())['data']

                # list of repo

                for repo in json_data:
                    commits = list(repo.values())[0]
                    with open(output_file.resolve(), 'a', newline='') as output_csv:

                        fieldnames = csv_headers
                        writer = csv.DictWriter(output_csv, fieldnames=fieldnames)

                        for commit in commits:
                            commit_normalization = pd.json_normalize(commit, sep='_')
                            writer.writerow(commit_normalization.to_dict())

if __name__ == "__main__":
    main()