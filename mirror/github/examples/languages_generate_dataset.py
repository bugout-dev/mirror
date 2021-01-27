
import os
import sys
from pathlib import Path
import nltk
import itertools
from nltk.tokenize.casual import casual_tokenize
import random
from sklearn.feature_extraction.text import CountVectorizer
import csv

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


def generate_datasets():
    print(os.environ)
    languages_folder = os.environ.get('LANGUAGES_REPOS')

    chunksize = 10

    output_folder = Path(languages_folder) / chunk_output_folder

    output_folder.mkdir(parents=True, exist_ok=True)

    output_csv = output_folder / f"result_{chunksize}_rows_snipet_dataset.csv"

    with output_csv.open( mode='wt', encoding='utf8', newline='') as output:
        fnames = ['snipet', 'lang', "datetime", "mirror_version"]
        writer = csv.DictWriter(output, fieldnames=fnames)
        writer.writeheader()   

        for lang in language_ext:
            lang_path = Path(languages_folder) / lang

            

            # create chunks
            language_chunks = chunking(lang_path,language_ext[lang],chunksize)

            
            for index,chunk in enumerate(language_chunks):

                chunk_path = output_folder / f"{index}.txt"

                with chunk_path.open('wt', encoding='utf-8') as chunk_file:
                    chunk_file.write(chunk)
                writer.writerow({'snipet' : chunk_path, 'lang': lang, "mirror_version": mirror_version})



if __name__ == "__main__":
    generate_datasets()
