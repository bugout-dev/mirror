
import os
import sys
import csv
import json
import click
import sqlite3
import itertools
from . import db_tool
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime




language_ext = {
    "CoffeeScript": ".coffee",
    "CSS": ".css",
    "Dart": ".dart",
    "Elixir": ".ex",
    "Go": ".go",
    "Groovy": ".groovy",
    "HTML": ".html",
    "Java": ".java",
    "Kotlin": ".kt",
    "Objective-C": ".m",
    "Perl": ".pl",
    "PHP": ".php",
    "PowerShell": ".sh",
    "Ruby": ".rb",
    "JavaScript": ".js",
    "Python": ".py",
}

chunk_output_folder = "test-chunk-3"

mirror_version = "0.1"


def searching_all_files(directory: Path,extention):

    """
    return list of file path inside folder
    """

    file_list = [] # A list for storing files existing in directories

    for x in directory.iterdir():
        if x.is_file() and extention in x.name:

           file_list.append(x)
        elif x.name.startswith('.') or x.is_file():
            continue
        else:

           file_list.extend(searching_all_files(directory/x,extention))

    return file_list


def chunking(lang_path, ext, chunksize):

    """
    Create chunks from given file extemtion and language
    """
    corpus = []
    for source_file in searching_all_files(lang_path, ext):
        try:
            with open(source_file, 'r',  encoding='utf8') as file_text:
                for next_n_lines in itertools.zip_longest(*[file_text] * chunksize):
                    if next_n_lines:
                        corpus.append("".join([i for i in next_n_lines if i]))
        
        except:
            continue
    return corpus



@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--result-dir', '-r', default='.', help='Dir for data.', show_default=True)
@click.option('--languages-file', '-f', help='Path to json file with languages for extracting.', required = True)
@click.option('--languages-dir', '-ld', help='Path to directory with languages repos.')
@click.option('--chunksize', '-cs', type=int, default=10, help='Size of code snipet.')
@click.option('--sqlite-path', '-sq', help='Sqlite for writing snipets.', default = None,  show_default=True)
def generate_datasets(result_dir: str, languages_file: str, languages_dir: str, chunksize: int, sqlite_path: Optional[str]):
    
    if not languages_dir:
        languages_folder = os.environ.get('LANGUAGES_REPOS')

    chunksize = chunksize


    if sqlite_path:
        conn = db_tool.create_connection(sqlite_path)
        db_tool.create_table_tasks(conn)

    if languages_file:
        try:
            langs_file = Path(languages_file)
            with langs_file.open('r', encoding='utf8') as langs:
                language_ext = json.load(langs)
        except Exception as err:
            print(f"Can't read languages file. Err: {err}")

    output_folder = Path(result_dir) / chunk_output_folder

    output_folder.mkdir(parents=True, exist_ok=True)

    output_csv = output_folder / f"result_{chunksize}_rows_snipet_dataset.csv"

    with output_csv.open( mode='wt', encoding='utf8', newline='') as output:
        fnames = ['snipet', 'lang']
        writer = csv.DictWriter(output, fieldnames=fnames)
        writer.writeheader()   

        for lang in language_ext:
            lang_path = Path(languages_folder) / lang
            if not lang_path.exists():
                continue
            

            # create chunks
            language_chunks = chunking(lang_path,language_ext[lang],chunksize)

            
            for index,chunk in enumerate(language_chunks):

                chunk_path = output_folder / f"{index}.txt"

                with chunk_path.open('wt', encoding='utf-8') as chunk_file:
                    chunk_file.write(chunk)
                writer.writerow({'snipet' : chunk_path, 'lang': lang})
                if sqlite_path:
                    db_tool.write_snipet_to_db(conn, chunk, lang)
    config = json.dumps({"mirror version" : "0.1.1",
                         "date": f"{datetime.datetime.now()}",
                         "langs_config":language_ext})



if __name__ == "__main__":
    generate_datasets()
