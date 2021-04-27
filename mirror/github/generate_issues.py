import base64
from collections import defaultdict
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Dict, Optional, Union
import zipfile

import click

from .data import CommitPublic, IssuesPublic

from . import db_tool
#from .. import settings



def get_issues_files(issues_dir):

    """
    Return list of files with repose by given ids range or all files from folder if ids range not set

    In order to make sure that all repositories are covered,
    add 2 additional files from the beginning of the ordered directory list and from the end

    """

    if not issues_dir:
        raise ("Empty repos dir.")
    issue_files = []

    # organization level
    for organization_dir in os.listdir(issues_dir):
        if os.path.isdir(os.path.join(issues_dir, organization_dir)):

            organization_repos_path = os.path.join(issues_dir, organization_dir)
            
            # repos level
            for repo_dir in  os.listdir(organization_repos_path):
                if os.path.exists(os.path.join(organization_repos_path, repo_dir, "issues")):
                    for issue in os.listdir(os.path.join(organization_repos_path, repo_dir, "issues")):
                        issue_files.append(os.path.join(organization_repos_path, repo_dir, "issues",issue))

    return issue_files

@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--crawldir", "-d", default=".", help='Path to save folder. default="." ')
@click.option("--issues-dir", "-i", help="Directory with output of issues crawl.")
def issues_generate(
    crawldir: str,
    issues_dir: str,
):
    files_for_proccessing = get_issues_files(issues_dir)

    conn = db_tool.create_connection(os.path.join(crawldir, "issues.db"))
    db_tool.create_issues_table(conn)

    issues_list = []
    fields = [
        "body",
        "title",
        "comments_url",
        "comments",
        "html_url",
        "state",
        "number",
        "author_association",
        "url",
        "repository_url",
        "labels_url",
        "events_url",
        "author_association",
        "created_at",
        "updated_at",
        "closed_at",
    ]

    
    with click.progressbar(files_for_proccessing, label="Download issues") as bar:
        for issue_file in bar:
            print(issue_file)

            try:
                with open(issue_file, 'r') as issue_file:
                    issue_meta = json.load(issue_file)
                    print(issue_meta.keys())
                    if "issue" in issue_meta.keys():
                        issue_meta = issue_meta['issue']
                        if "pull_request" in issue_meta:
                            continue

                        validate_value = IssuesPublic(**issue_meta).dict()
                        issues_list.append([validate_value[i] if i in validate_value else None for i in fields])
                    elif "issues" in issue_meta.keys():
                        issues_meta = issue_meta['issues']
                        for issue_meta in issues_meta:
                            if "pull_request" in issue_meta:
                                continue
                            validate_value = IssuesPublic(**issue_meta).dict()
                            issues_list.append([validate_value[i] if i in validate_value else None for i in fields])
                    if len(issues_list)> 500:
                        db_tool.write_issue_to_db(conn, issues_list)
                        issues_list.clear()
                    
            except Exception as err:
                print(issue_file)
                print(err)
                raise
        if len(issues_list) > 0:
            db_tool.write_issue_to_db(conn, issues_list)


if __name__ == "__main__":
    issues_generate()