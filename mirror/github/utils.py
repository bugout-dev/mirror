import os
import csv
import json
from pathlib import Path

import click


def get_nearest_value(iterable, value):
    """
    simple return nearest value inside given iterable object
    """
    return min(iterable, key=lambda x: abs(int(x.split(".")[0]) - value))


def read_command_type(path):
    """
    Return type of command wich generated repos inside repos folder
    """
    with open(path, "r", encoding="utf8") as first_file:
        data = json.loads(first_file.read())
    return data["command"]


def forward_languages_config(input_config, output_dir):
    """
    Create languages config inside output for simplify pipelinr
    """

    with open(input_config, "r", encoding="utf8") as config_file:
        config = json.load(config_file)

    with open(
        os.path.join(output_dir, "languages_config.json"), "a", encoding="utf8"
    ) as config_file:
        json.dump(config, config_file)


def write_with_size(json_list, file_index, path):
    """
    Return current size after writing
    """

    file_path = os.path.join(path, f"{file_index}.json")

    with open(file_path, "r+", newline="", encoding="utf8") as file:
        data = json.load(file)
        data['data'].extend(json_list)
        json.dump(data, file)
        size_of_file = file.tell()
    return size_of_file


def flatten_json(y):
    out = {}

    def flatten(x, name=""):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + "_")
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + "_")
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--json-files-folder",
    "-p",
    default=".",
    help="folders with repo/commits.",
    show_default=True,
)
@click.option("--output-csv", "-f", help="Output csv normilize file.")
@click.option("--command", "-t", help="specify wich type of content need extract.")
def json_files_to_csv(command: str, path_input_folder: str, path_output_csv: str):
    """
    Generate one csv file from json files

    """

    inputs_path = Path(path_input_folder)

    output_file = Path(path_output_csv)
    print(inputs_path.is_dir(), output_file.exists())

    if not inputs_path.is_dir():
        return

    if command == "commits":

        json_list = [file for file in os.listdir(inputs_path) if "commits" in file]

        # init csv
        read_file = inputs_path / json_list[0]

        with open(read_file, "r") as income, open(
            output_file, "a", newline=""
        ) as csv_out:
            json_data = json.loads(income.read())["data"]
            print(json_data[0].keys())
            first_repo = list(json_data[0].keys())[0]
            commit = json_data[0][first_repo][0]

            # generate commit header

            standart_commit = flatten_json(commit)

            csv_headers = standart_commit.keys()
            fieldnames = csv_headers
            print(fieldnames)
            writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
            writer.writeheader()

        print(len(json_list))
        # list of files
        for json_file in json_list:
            read_file = inputs_path / json_file

            with open(read_file, "r", encoding="utf-8") as income:
                print(read_file)
                try:
                    json_data = json.loads(income.read())["data"]
                except:
                    print("not processed")

                # list of repo

                for repo in json_data:
                    commits = list(repo.values())[0]
                    with open(
                        output_file.resolve(), "a", newline="", encoding="utf8"
                    ) as output_csv:

                        fieldnames = csv_headers
                        writer = csv.DictWriter(
                            output_csv, fieldnames=fieldnames, extrasaction="ignore"
                        )

                        for commit in commits:
                            commit_normalization = flatten_json(commit)

                            writer.writerow(commit_normalization)


if __name__ == "__main__":
    json_files_to_csv()
