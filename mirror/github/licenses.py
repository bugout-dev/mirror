"""
Collect license information for a repository or a list of repositories
"""

import argparse
import json
import os
import sys
import click
import time
from typing import Any, Dict, List

import requests
from tqdm import tqdm # type: ignore

subcommand = "licenses"

def get_license(repo_api_url: str) -> Dict[str, Any]:
    """
    Gets the license for the repository at the given GitHub API URL.

    Args:
    repo_api_url
        GitHub API URL for a repository. These are of the form:
        https://api.github.com/repos/:owner/:name
        This URL is allowed to have a trailing slash.

    Returns: JSON-serializable dictionary of the form:
    {'ending_rate_limit': <rate limit after the query>, 'data': <license info>}
    """
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'simiotics mirror',
    }
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token is not None and github_token != '':
        headers['Authorization'] = f'token {github_token}'

    if repo_api_url[-1] == '/':
        repo_api_url = repo_api_url[:-1]

    license_url = f'{repo_api_url}/license'

    r = requests.get(license_url, headers)
    ending_rate_limit_raw = r.headers.get('X-RateLimit-Remaining', '')
    try:
        ending_rate_limit = int(ending_rate_limit_raw)
    except:
        ending_rate_limit = -1

    result: Dict[str, Any] = {
        'ending_rate_limit': ending_rate_limit,
        'data': r.json(),
    }
    return result

@click.command(context_settings={
    "ignore_unknown_options": True,
    "help_option_names": ['-h', '--help']
})
@click.option('--repos', '-r', help='File with JSON array of GitHub API URLs for repos (if value is "file:<filename>") '
            'OR comma-separated list of GitHub API URLs of repos')

@click.option('--interval', '-t', type=float, default=0.01, help='Number of seconds to wait between page retrievals from /repositories endpoint')

@click.option('--min-rate-limit',  '-l', type=int, default=30, help='Minimum remaining rate limit on API under which the crawl is interrupted')

@click.option('--outfile', '-o', default=30, help='File to which to write license information as JSON lines, one per repository')

def licenses_handler(repos_json: str, interval: float, min_rate_limit: int, outfile: str) -> None:
    """
    Handler for licenses subcommand

    Args:
    args
        argparse namespace representing arguments to "mirror github licenses" command parse from
        the command line

    Returns: None, prints license information for the repositories in args.repos to stdout or to the
    file specified by args.outfile
    """
    repos: List[str] = []
    if repos_json[:len('file:')] == 'file:':
        infile = repos_json[len('file:'):]
        with open(infile, 'r') as ifp:
            repos = json.load(ifp)
    else:
        repos = repos_json.split(',')

    ofp = sys.stdout
    if outfile is not None:
        ofp = open(outfile, 'w')

    for repo in repos:
        time.sleep(interval)
        result = get_license(repo)
        print(json.dumps(result), file=ofp)
        if result['ending_rate_limit'] < min_rate_limit:
            break

    if outfile is not None:
        ofp.close()