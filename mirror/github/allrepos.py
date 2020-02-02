"""
Collect metadata for all GitHub repositories readable to the given token.

Support checkpointing against a small state object - the integer ID of the last repository seen.
"""

import argparse
import json
import glob
import os
import random
import sys
import time
from typing import Any, Callable, Dict, Iterator, List, Optional, TextIO

import requests

from ..populate import populate_cli

subcommand = 'allrepos'

REPOSITORIES_URL = 'https://api.github.com/repositories'
REMAINING_RATELIMIT_HEADER = 'X-RateLimit-Remaining'

def crawl(start_id: int, max_id: int, interval: float, min_rate_limit: int) -> Dict[str, Any]:
    """
    Crawls the /repositories endpoint of the GitHub API until it hits a page on which the maximum ID
    is greater than or equal to the given max_id parameter, at which point, it returns the results
    of the crawl as a Python dictionary.

    Args:
    start_id
        Last ID seen when crawling the public repositories
    max_id
        Crawl should end after encountering repositories of ID greater than or equal to this number
    interval
        Number of seconds (fractional OK) for which to wait between API requests. This is to help
        with rate-limiting.
    min_rate_limit
        If the X-RateLimit-Remaining header on any response is less than this number, stop crawling
        and return right away.
    """
    result = {
        'start_id': start_id,
        'max_id': max_id,
        'data': [],
        'start': int(time.time()),
    }

    headers = {
        'User-Agent': 'simiotics mirror',
    }
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token is not None:
        headers['Authorization'] = f'token {github_token}'

    since = start_id
    curr_rate_limit = min_rate_limit + 10
    while since is not None and since < max_id and curr_rate_limit > min_rate_limit:
        time.sleep(interval)
        r = requests.get(REPOSITORIES_URL, params={'since': since}, headers=headers)
        response_body = r.json()
        if len(response_body) == 0:
            break

        result['data'].extend(response_body) # type: ignore
        since = response_body[-1].get('id')

        curr_rate_limit_raw = r.headers.get(REMAINING_RATELIMIT_HEADER)
        try:
            curr_rate_limit = -1
            if curr_rate_limit_raw is not None:
                curr_rate_limit = int(curr_rate_limit_raw)
        except:
            break

    result['max_id'] = since
    result['end'] = int(time.time())
    result['ending_rate_limit'] = curr_rate_limit

    return result

def crawl_handler(args: argparse.Namespace) -> None:
    """
    Processes arguments as parsed from the command line and uses them to run a crawl of the GitHub
    /repositories endpoint.

    Results are stored as JSON file in the output directory specified in the arguments.

    Args:
    args
        argparse.Namespace object containing commands to the allrepos command parser passed from
        command line

    Returns: None
    """
    next_id = nextid(args.crawldir)
    current_max = max(args.start_id, next_id)
    while current_max < args.max_id:
        result = crawl(
            current_max,
            min(current_max + args.batch_size, args.max_id),
            args.interval,
            args.min_rate_limit,
        )
        outfile = os.path.join(args.crawldir, f'{current_max}.json')
        with open(outfile, 'w') as ofp:
            json.dump(result, ofp)

        if len(result['data']) == 0:
            break
        current_max = result['data'][-1]['id']

        if result['ending_rate_limit'] < args.min_rate_limit:
            break

def crawl_populator(parser: argparse.ArgumentParser) -> None:
    """
    Populates parser with crawl parameters

    Args:
    parser
        Argument parser representing crawl functionality

    Returns: None
    """
    parser.add_argument(
        '--start-id',
        '-s',
        type=int,
        default=0,
        help='Last ID seen in GitHub all repos crawl; current crawl will start from its successor',
    )
    parser.add_argument(
        '--max-id',
        '-m',
        type=int,
        default=100000000,
        help='Crawl should extend to this idea (and no more than one page further)',
    )
    parser.add_argument(
        '--interval',
        '-t',
        type=float,
        default=1.0,
        help='Number of seconds to wait between page retrievals from /repositories endpoint',
    )
    parser.add_argument(
        '--min-rate-limit',
        '-l',
        type=int,
        default=30,
        help='Minimum remaining rate limit on API under which the crawl is interrupted',
    )
    parser.add_argument(
        '--batch-size',
        '-n',
        type=int,
        default=3000,
        help='Number of pages  should (roughly) be processed before writing results to disk',
    )
    parser.add_argument(
        '--crawldir',
        '-d',
        required=True,
        help='Path to directory in which crawl results should be written',
    )
    parser.set_defaults(func=crawl_handler)

def nextid(crawldir: str) -> int:
    """
    Given a directory containing only JSON files produced by an allrepos crawl, this function
    returns the maximum ID seen in that crawl.

    Args:
    crawldir
        Output directory for an allrepos crawl

    Returns: Maximum ID over all repositories seen in the crawl
    """
    result_files = glob.glob(os.path.join(crawldir, '*.json'))
    if not result_files:
        return 0
    indexed_result_files = [
        (
            rfile,
            int(os.path.basename(rfile).split('.')[0])
        ) for rfile in result_files
    ]
    last_file, index = max(indexed_result_files, key=lambda p: p[1])
    with open(last_file, 'r') as ifp:
        result = json.load(ifp)
    if len(result['data']) == 0:
        return index
    return result['data'][-1]['id']

def nextid_handler(args: argparse.Namespace) -> None:
    """
    Prints ID of most recent repository crawled and written to the crawldir parsed into the given
    argparse args object.

    Args:
    args
        Namespace containing arguments parsed from command line

    Returns: None. Prints most recent repository ID to screen.
    """
    print(nextid(args.crawldir))

def nextid_populator(parser: argparse.ArgumentParser) -> None:
    """
    Populates parser with nextid parameters

    Args:
    parser
        Argument parser representing nextid functionality

    Returns: None
    """
    parser.add_argument(
        '--crawldir',
        '-d',
        required=True,
        help='Path to directory in which crawl results should be written',
    )
    parser.set_defaults(func=nextid_handler)

def sample(crawldir: str, choose_probability: float) -> Iterator[Dict[str, Any]]:
    """
    Given a directory containing only JSON files produced by an allrepos crawl, this generator
    yields the next sample.

    NOTE: Not what I expected, but much faster than the following command:
    $ cat ~/data/mirror/allrepos/*.json | \
        jq -rc ".data[]" | \
        awk 'BEGIN {srand()} !/^$/ { if (rand() <= 0.01) print $0 }' \
        >outfile.jsonl

    awk bit comes from here:
    https://stackoverflow.com/questions/692312/randomly-pick-lines-from-a-file-without-slurping-it-with-unix

    Args:
    crawldir
        Output directory for an allrepos crawl
    choose_probability
        Probability with which any single document is chosen for the sample

    Returns: JSON array containing the sampled repositories
    """
    assert 0 <= choose_probability <= 1

    crawl_batches = glob.glob(os.path.join(crawldir, '*.json'))
    for batch in crawl_batches:
        with open(batch, 'r') as ifp:
            result = json.load(ifp)
        for repository in result['data']:
            if random.random() < choose_probability:
                yield repository

def sample_handler(args: argparse.Namespace) -> None:
    """
    Writes repositories sampled from a crawl directory to an output file in JSON lines format

    Args:
    args
        Namespace containing arguments parsed from command line

    Returns: None
    """
    ofp = sys.stdout
    if args.outfile is not None:
        ofp = open(args.outfile, 'w')

    try:
        samples = sample(args.crawldir, args.probability)
        for repository in samples:
            print(json.dumps(repository), file=ofp)
    finally:
        ofp.close()

def sample_populator(parser: argparse.ArgumentParser) -> None:
    """
    Populates parser with nextid parameters

    Args:
    parser
        Argument parser representing nextid functionality

    Returns: None
    """
    parser.add_argument(
        '--crawldir',
        '-d',
        required=True,
        help='Path to directory in which crawl results should be written',
    )
    parser.add_argument(
        '--outfile',
        '-o',
        help='Path to file to which samples should be written (default: stdout)',
    )
    parser.add_argument(
        '--probability',
        '-p',
        type=float,
        required=True,
        help='Probability with which a repository in the crawl directory should be chosen',
    )
    parser.set_defaults(func=sample_handler)

def populator(parser: argparse.ArgumentParser) -> None:
    """
    Populates parser with allrepos and children

    Args:
    parser
        Argument parser representing allrepos functionality

    Returns: None
    """
    subcommands: Dict[str, Callable[[argparse.ArgumentParser], None]] = {
        'crawl': crawl_populator,
        'nextid': nextid_populator,
        'sample': sample_populator,
    }
    populate_cli(parser, subcommands)
