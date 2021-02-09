
import os
import sys
import csv
import json
import click
import base64
import sqlite3
import itertools
from . import db_tool
from pathlib import Path
from .utils import write_with_size
from typing import Tuple, Optional
from datetime import datetime
from .. import settings

 

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
@click.option('--sqlite-path', '-sq', help='Sqlite for writing snippets.', default = None,  show_default=True)
def generate_datasets(result_dir: str, languages_file: str, languages_dir: str, chunksize: int, sqlite_path: Optional[str]):
    

    file_size_limit = 500000

    if not languages_dir:
        languages_folder = os.environ.get('LANGUAGES_REPOS')


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
    start_block = '{'+ f'data": ['

    end_block = ']}'

    output_csv = os.path.join(result_dir, f"{chunksize}_rows_snipet_dataset.csv")



    with output_csv.open( mode='wt', encoding='utf8', newline='') as output:

        fnames = ['snipet', 'index', 'lang']
        writer = csv.DictWriter(output, fieldnames=fnames)
        writer.writeheader() 
  
        file_index = 1 # start index

        for lang in languages_ext:
            lang_path = os.path.join(languages_folder, lang)

            if not lang_path.exists():
                continue

            chunk_index = 0
            
            output_lang_dir = os.path.join(output_folder, lang)
            # create chunks recursive read all files and return list of chunks

            if not os.path.exists(crawldir):
                os.makedirs(crawldir)

            language_chunks = chunking(lang_path,languages_ext[lang],chunksize)

            if not language_chunks:
                continue
            
            write_with_size(start_block, file_index, output_lang_dir)

            for i,chunk in enumerate(language_chunks):

                

                try:
                    # writing and return file size
                    current_size =  write_with_size( f'"{base64.b64encode(chunk.encode("utf8"))}"', file_index, output_lang_dir)
                    
                    # add path csv
                    writer.writerow({'snipet' : os.path.join(output_lang_dir, f"{file_index}.json"),
                                     'index': chunk_index,
                                     'lang': lang})
                    
                    if sqlite_path:
                        db_tool.write_snipet_to_db(conn, chunk, lang)

                    # create new file and restar chunk indexing
                    if current_size > file_size_limit:
                        write_with_size(end_block, file_index, output_lang_dir)
                        file_index += 1
                        chunk_index = 0
                        write_with_size(start_block, file_index, output_lang_dir)
                    else:
                        # if it last lang chunk so close
                        if i != len(language_chunks) - 1:
                            write_with_size(',', file_index, output_lang_dir)

                    chunk_index += 1
                
                except KeyboardInterrupt:
                    raise('CTRL+C')

                except Exception as err:
                    print(err)
                    continue

    config = json.dumps({"mirror version" : settings.module_version,
                         "date": f"{datetime.now()}",
                         "langs_config": languages_ext})



if __name__ == "__main__":
    generate_datasets()
