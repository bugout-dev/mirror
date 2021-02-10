
import os
import sys
import csv
import json
import glob
import base64
import tarfile
import sqlite3
import itertools
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional

import click

from . import db_tool
from .. import settings
from .utils import write_with_size



class ReadReposDirectoryError(Exception):
    """Raised when repos folder not set."""
    pass

def create_tar_file(files_dir, output_dir):
    """
    Crate tar from files inside commits folder
    """
    with tarfile.open(os.path.join(output_dir, 'snippets.tar.gz'), 'w') as archive:
        # for i in os.listdir(commits_folder):
        #    archive.add(i, filter=lambda x: x if x.name.endswith('.json') else None)
        archive.add(files_dir)

def searching_all_files(directory, extention: str):

    """
    return list of file path inside folder
    """

    file_list = [] # A list for storing files existing in directories
    dir = Path(directory)
    for x in dir.iterdir():
        if x.is_file() and extention in x.name:

           file_list.append(x)
        elif x.name.startswith('.') or x.is_file():
            continue
        else:

           file_list.extend(searching_all_files(dir/x,extention))

    return file_list


def chunking(lang_path, ext: str, chunksize: int):

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
        except KeyboardInterrupt:
            raise KeyboardInterrupt('CTRL+C')
        except:
            continue
    return corpus



@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--result-dir', '-r', default='.', help='Dir for data.', show_default=True)
@click.option('--languages-file', '-f', help='Path to json file with languages for extracting.', required = True)
@click.option('--languages-dir', '-L', help='Path to directory with languages repos.')
@click.option('--chunksize', '-s', type=int, default=10, help='Size of code snipet.')
@click.option('--sqlite-path', '-q', help='Sqlite for writing snippets.', default = None,  show_default=True)
def generate_datasets(result_dir: str, languages_file: str, languages_dir: Optional[str], chunksize: int, sqlite_path: Optional[str]):
    

    file_size_limit = 500000

    if not languages_dir:
        languages_dir = os.environ.get('LANGUAGES_REPOS')
        if not languages_dir:
            raise ReadReposDirectoryError('LANGUAGES_REPOS not set.')


    if sqlite_path:
        conn = db_tool.create_connection(sqlite_path)
        db_tool.create_table_tasks(conn)
    

    # Read languages file
    if languages_file:
        try:
            langs_file = Path(languages_file)
            with langs_file.open('r', encoding='utf8') as langs:
                languages_ext = json.load(langs)
        except Exception as err:
            print(f"Can't read languages file. Err: {err}")
            raise
    
    

    # Create separate folder

    snippets_dir = os.path.join(result_dir, "snippets")

    if not os.path.exists(snippets_dir):
        os.makedirs(snippets_dir)

    # Create file with path to chunk
    start_block = '{"data": ['

    end_block = ']}'

    output_csv = Path(result_dir) / f"{chunksize}_rows_snipet_dataset.csv"



    with open(output_csv, mode='wt', encoding='utf8', newline='') as output:

        fnames = ['snipet', 'index', 'lang']
        writer = csv.DictWriter(output, fieldnames=fnames)
        writer.writeheader() 
  
        file_index = 1 # start index

        for lang in languages_ext:
            lang_path = Path(languages_dir) / lang

            if not os.path.exists(lang_path):
                continue

            chunk_index = 0
            
            output_lang_dir = Path(snippets_dir) / lang
            # create chunks recursive read all files and return list of chunks

            if not os.path.exists(output_lang_dir):
                os.makedirs(output_lang_dir)

            language_chunks = chunking(lang_path,languages_ext[lang],chunksize)
            print(f"Crated {len(language_chunks)} {lang} chanks.")

            if not language_chunks:
                continue
            
            write_with_size(start_block, file_index, output_lang_dir)

            for i,chunk in enumerate(language_chunks):

                try:
                    # writing and return file size
                    current_size =  write_with_size(''.join(('"',str(base64.b64encode(chunk.encode("utf8"))),'"')),
                                                    file_index,
                                                    output_lang_dir)
                    
                    # add path csv
                    writer.writerow({'snipet' : os.path.join("snippets", lang.capitalize(), f"{file_index}.json"),
                                     'index': chunk_index,
                                     'lang': lang})
                    
                    if sqlite_path:
                        db_tool.write_snipet_to_db(conn, chunk, lang)

                    # create new file and restar chunk indexing
                    if current_size > file_size_limit and i != len(language_chunks) :
                        write_with_size(end_block, file_index, output_lang_dir)
                        file_index += 1
                        chunk_index = 0
                        write_with_size(start_block, file_index, output_lang_dir)
                    elif i == len(language_chunks):
                        write_with_size(end_block, file_index, output_lang_dir)
                        file_index += 1
                        chunk_index = 0
                    else:
                        write_with_size(',', file_index, output_lang_dir)

                    chunk_index += 1
                
                except KeyboardInterrupt:
                    raise KeyboardInterrupt('CTRL+C')

                except Exception as err:
                    print(err)
                    continue
    
    create_tar_file(snippets_dir, result_dir)
    
    with open(Path(result_dir) / f"meta.json", 'w') as meta_out:
        json.dump({"mirror version" : settings.module_version,
                         "date": f"{datetime.now()}",
                         "langs_config": languages_ext}, meta_out)




if __name__ == "__main__":
    generate_datasets()
