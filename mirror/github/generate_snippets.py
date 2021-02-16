
import os
import sys
import csv
import json
import glob
import base64
#import tarfile
import zipfile
import sqlite3
import traceback
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

def create_zip_file(files_dir):
    """
    Create zip inside snippets folder
    """
    with zipfile.ZipFile(os.path.join(files_dir, '..','snippets.zip'), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(files_dir):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(files_dir, '..')))



def searching_all_files(directory, extention: str):

    """
    return list of file path inside folder
    """

    file_list = [] # A list for storing files existing in directories
    dir = Path(directory)
    for x in dir.iterdir():
        if x.is_file() and x.name.split('.')[-1] in extention:
           file_list.append(x)
        elif x.name.startswith('.') or x.is_file():
            continue
        else:

           file_list.extend(searching_all_files(dir/x,extention))

    return file_list

def chunk_encode(iterable_lines):
    return base64.b64encode("".join(iterable_lines).encode("utf8")).decode("utf8")


def chunking(repo_path, ext: str, chunksize: int, lines_step: int, common_path):

    """
    Create chunks from given file extemtion and language
    """
    corpus = []

    for source_file in searching_all_files(repo_path, ext):

        try:
                            
            line_number = 0
            with open(source_file, 'r',  encoding='utf8') as file_text:

                file_lines =  file_text.readlines()
                while line_number <= len(file_lines) - 1 - chunksize:
                    corpus.append({"file_name": os.path.relpath(file_text.name, common_path),
                                   "start_line": line_number,
                                   "chunk": chunk_encode(file_lines[line_number: line_number + chunksize])})
                    line_number += lines_step
                
                corpus.append({"file_name": os.path.relpath(file_text.name, common_path),
                               "start_line": line_number,
                               "chunk": chunk_encode(file_lines[line_number:])})
        
        except KeyboardInterrupt:
            raise KeyboardInterrupt('CTRL+C')
        except:
            traceback.print_exc()
            continue
    return corpus



@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--crawldir', '-d', default='.', help='Snippets output filder.', show_default=True)
@click.option('--languages-dir', '-L', help='Path to directory with languages repos.')
@click.option('--chunksize', '-c', type=int, default=10, help='Size of code snipet.')
@click.option('--rows-step', '-r', type=int, default=None, help='Distance between start rows.')
@click.option('--sqlite-path', '-q', help='Sqlite for writing snippets.', default = None,  show_default=True)
def generate_datasets(crawldir: str, languages_dir: Optional[str], chunksize: int, sqlite_path: Optional[str], rows_step: Optional[int]):
    
    """
    Create snippets dataset from cloned repos
    """

    file_size_limit = 500000

    if not rows_step:
        rows_step = chunksize

    if not languages_dir:
        languages_dir = os.environ.get('LANGUAGES_REPOS')
        if not languages_dir:
            raise ReadReposDirectoryError('LANGUAGES_REPOS not set.')


    if sqlite_path:
        conn = db_tool.create_connection(sqlite_path)
        db_tool.create_table_tasks(conn)
    

    # Read languages file
    try:
        langs_file = Path(languages_dir) / "languages_config.json"
        with langs_file.open('r', encoding='utf8') as langs:
            languages_ext = json.load(langs)
    except Exception as err:
        print(f"Can't read languages file. Err: {err}")
        raise
    
    

    # Create separate folder

    snippets_dir = os.path.join(crawldir, "snippets")

    if not os.path.exists(snippets_dir):
        os.makedirs(snippets_dir)

    # Create file with path to chunk
    start_block = '{"data": ['

    end_block = ']}'

    output_csv = Path(snippets_dir) / f"snippets.csv"



    with open(output_csv, mode='wt', encoding='utf8', newline='') as output:

        fnames = ['file', 'index', 'language', 'repo_file_name', 'github_repo_url', 'license', 'commit_hash', 'starting_line_number']
        writer = csv.DictWriter(output, fieldnames=fnames)
        writer.writeheader() 
  
        file_index = 1 # start index
        chunk_index = 0

        for lang in languages_ext:
            lang_path = Path(languages_dir) / lang

            if not os.path.exists(lang_path):
                continue

            #for repo in  [x[0] for x in os.walk(directory)]:

            meta_path = lang_path / "meta.json"

            with open(meta_path, 'r') as repos_meta_file:
                repos_meta = json.load(repos_meta_file)


            for repo in repos_meta["repos"]:
                license = None

                if repo['license']:
                   license =  repo['license']['spdx_id']

                language_chunks = chunking(os.path.join(lang_path,repo['name']),
                                        languages_ext[lang],
                                        chunksize,
                                        rows_step,
                                        languages_dir)
                print(f"Created {len(language_chunks)} {lang} chanks.")

                if not language_chunks:
                    continue
                
                write_with_size(start_block, file_index, snippets_dir)
                # github_repo_url, commit_hash, license
                for i,chunk_data in enumerate(language_chunks):

                    #for chunk in enumerate(language_chunks[chunk_file]):

                    try:
                        # writing and return file size
                        current_size =  write_with_size(''.join(('"',chunk_data["chunk"],'"')),
                                                        file_index,
                                                        snippets_dir)
                        
                        # add path csv
                        writer.writerow({'github_repo_url': repo["github_repo_url"],
                                        'commit_hash': repo['commit_hash'],
                                        'license': license,
                                        'file' : os.path.join( f"{file_index}.json"),
                                        'index': chunk_index,
                                        'language': lang.lower(),
                                        "repo_file_name": chunk_data["file_name"],
                                        "starting_line_number": chunk_data["start_line"]})
                        
                        if sqlite_path:
                            db_tool.write_snipet_to_db(conn, chunk_data["chunk"], lang)

                        # create new file and restar chunk indexing
                        if current_size > file_size_limit and i != len(language_chunks) :
                            write_with_size(end_block, file_index, snippets_dir)
                            file_index += 1
                            chunk_index = 0
                            write_with_size(start_block, file_index, snippets_dir)
                        elif i == len(language_chunks)-1:
                            write_with_size(end_block, file_index, snippets_dir)
                            file_index += 1
                            chunk_index = 0
                        else:
                            write_with_size(',', file_index, snippets_dir)

                        chunk_index += 1
                    
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt('CTRL+C')

                    except Exception as err:
                        print(err)
                        continue
                write_with_size(end_block, file_index, snippets_dir)
                file_index += 1
                chunk_index = 0

    create_zip_file(snippets_dir)
    
    with open(Path(snippets_dir)/ '..' / f"meta.json", 'w') as meta_out:
        # chunksize: int, sqlite_path: Optional[str], rows_step: Optional[int]
        json.dump({"mirror version" : settings.module_version,
                         "date": f"{datetime.now()}",
                         "languages init config": languages_ext,
                         "chunksize": chunksize,
                         "rows_step": rows_step}, meta_out)




if __name__ == "__main__":
    generate_datasets()
