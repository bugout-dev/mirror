import os
import sys
import csv
import json
import glob
import base64

# import tarfile
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



class ChunkLoader():

    def __init__(self, repo_path, ext, chunksize, rows_step, batch_size, common_path):
        self.line_index = 0
        self.file_index = 0
        self.chunk_size = chunksize
        self.rows_step = rows_step
        self.files = searching_all_files(repo_path, ext)
        self.batch_size = batch_size
        self.common_path = common_path

    def get_next_chunks(self):
        chunks = []
        
        while True:

            if self.file_index == len(self.files):
                return chunks
            
            
            try:
                # TODO: need think about encoding becuse it's normal case use cp1252 for powershel scripts
                try:
                    with open(self.files[self.file_index], "r", encoding="utf-8") as file_text:

                        file_lines = file_text.readlines()
                except:
                    with open(self.files[self.file_index], "r", encoding="cp1252") as file_text:

                        file_lines = file_text.readlines()
                
                file_path = os.path.relpath(self.files[self.file_index], self.common_path)
                print(file_path)
                while self.line_index <= len(file_lines) - 1 - self.chunk_size:

                    if self.line_index + self.chunk_size >= len(file_lines):
                        snippet = "".join(file_lines[self.line_index:])
                    else:
                        snippet = "".join(file_lines[self.line_index : self.line_index + self.chunk_size])

                    chunks.append(
                        {
                            "file_name": file_path,
                            "start_line": self.line_index,
                            "chunk": snippet
                        }
                    )

                    self.line_index += self.rows_step

                    if len(chunks) == self.batch_size:
                        return chunks


            except KeyboardInterrupt:
                raise KeyboardInterrupt("CTRL+C")
            except:
                traceback.print_exc()
                continue
 
            
            self.line_index = 0
            self.file_index += 1


        return chunks


class ConfigFileNotFoundError(Exception):
    """Raised when language config file with file extention not applied."""

    pass


class ReadReposDirectoryError(Exception):
    """Raised when repos folder not set."""

    pass


def create_zip_file(files_dir):
    """
    Create zip inside snippets folder
    """
    with zipfile.ZipFile(
        os.path.join(files_dir, "..", "snippets.zip"), "w", zipfile.ZIP_DEFLATED
    ) as zipf:
        for root, dirs, files in os.walk(files_dir):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(
                        os.path.join(root, file), os.path.join(files_dir, "..")
                    ),
                )


def searching_all_files(directory, extention: str):

    """
    return list of file path inside folder
    """

    file_list = []  # A list for storing files existing in directories
    dir = Path(directory)
    for x in dir.iterdir():
        if x.is_file() and x.name.split(".")[-1] in extention:
            file_list.append(x)
        elif x.name.startswith(".") or x.is_file():
            continue
        else:

            file_list.extend(searching_all_files(dir / x, extention))

    return file_list


def chunk_encode(iterable_lines):
    return base64.b64encode("".join(iterable_lines).encode("utf8")).decode("utf8")


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--crawldir", "-d", default=".", help="Snippets output filder.", show_default=True
)
@click.option("--languages-dir", "-L", help="Path to directory with languages repos.")
@click.option("--chunksize", "-c", type=int, default=10, help="Size of code snippet.", show_default=True)
@click.option(
    "--rows-step", "-s", type=int, default=None, help="Distance between start rows."
)
@click.option(
    "--batch-size",
    "-b",
    help="Amount of snippets writing to db per transaction.",
    type=int,
    default=1000,
    show_default=True,
)
@click.option(
    "--languages-file",
    "-f",
    default=None,
    help="Path to json file with languages for extracting.",
)
def generate_datasets(
    crawldir: str,
    languages_dir: Optional[str],
    chunksize: int,
    batch_size: int,
    rows_step: Optional[int],
    languages_file: str,
):

    """
    Create snippets dataset from cloned repos
    """

    if not rows_step:
        rows_step = chunksize

    if not languages_dir:
        languages_dir = os.environ.get("LANGUAGES_DIR")
        if not languages_dir:
            raise ReadReposDirectoryError("LANGUAGES_DIR not set.")

    # Read languages config file
    try:
        if not languages_file:
            if not os.path.exists(Path(languages_dir) / "languages_config.json"):
                raise ConfigFileNotFoundError("Config file not found.")
            else:
                langs_file = Path(languages_dir) / "languages_config.json"
        else:

            langs_file = Path(languages_file)
        with langs_file.open("r", encoding="utf8") as langs:
            languages_ext = json.load(langs)
    except Exception as err:
        print(f"Can't read languages file. Err: {err}")
        raise

    # Create separate folder

    snippets_dir = os.path.join(crawldir, "snippets")

    if not os.path.exists(snippets_dir):
        os.makedirs(snippets_dir)

    # Create connection
    conn = db_tool.create_connection(os.path.join(snippets_dir, "snippets.db"))
    db_tool.create_snippets_table(conn)

    for lang in languages_ext:

        lang_path = os.path.join(languages_dir, lang)

        meta_path = os.path.join(lang_path, "meta.json")

        if not os.path.exists(meta_path):
            continue

        with open(meta_path, "r") as repos_meta_file:
            repos_meta = json.load(repos_meta_file)

        for repo in repos_meta["repos"]:
            license = None

            print(repo['name'])
            
            loader = ChunkLoader(                
                os.path.join(lang_path, repo["name"]),
                languages_ext[lang],
                chunksize,
                rows_step,
                batch_size,
                languages_dir)

           

            if repo["license"]:
                license = repo["license"]["spdx_id"]

            while True:
                try:
                    chunks = loader.get_next_chunks()

                    batch = [(repo["github_repo_url"],
                            repo["commit_hash"],
                            chunk_data["chunk"],
                            license,
                            lang.lower(),
                            Path(chunk_data["file_name"]).name,
                            chunk_data["start_line"]) for chunk_data in chunks]

                    db_tool.write_snippet_to_db(conn, batch)


                    if not chunks:
                        break
                
                except KeyboardInterrupt:
                    raise KeyboardInterrupt("CTRL+C")

                except Exception as err:
                    print(err)
                    raise

    create_zip_file(snippets_dir)

    with open(Path(snippets_dir) / ".." / f"meta.json", "w") as meta_out:

        json.dump(
            {
                "mirror version": settings.module_version,
                "date": f"{datetime.now()}",
                "languages init config": languages_ext,
                "chunksize": chunksize,
                "rows_step": rows_step,
            },
            meta_out,
        )


if __name__ == "__main__":
    generate_datasets()
