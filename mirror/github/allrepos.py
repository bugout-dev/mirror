"""
Collect metadata for all GitHub repositories readable to the given token.

Support checkpointing against a small state object - the integer ID of the last repository seen.
"""

import argparse
import csv
import json
import glob
import multiprocessing
import os
import random
import sys
import time
from typing import Any, Callable, Dict, Iterator, List, Optional, TextIO, Tuple

import click

import requests
from tqdm import tqdm

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
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'simiotics mirror',
    }
    github_token = os.environ.get('GITHUB_TOKEN')
    if github_token is not None and github_token != '':
        headers['Authorization'] = f'token {github_token}'

    since = start_id
    curr_rate_limit = min_rate_limit + 10
    while since is not None and since < max_id and curr_rate_limit > min_rate_limit:
        time.sleep(interval)
        r = requests.get(REPOSITORIES_URL, params={'since': since}, headers=headers)
        response_body = r.json()
        if not response_body:
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
    result['command'] = "crawl"
    result['ending_rate_limit'] = curr_rate_limit

    return result


@click.command(context_settings={
    "ignore_unknown_options": True
})
@click.option('--start-id', '-s', type=int, default=0, help='Last ID seen in GitHub all repos crawl; current crawl will start from its successor')

@click.option('--max-id', '-m', type=int, default=100000000, help='Crawl should extend to this idea (and no more than one page further)')

@click.option('--interval',  '-t', type=float, default=1.0, help='Number of seconds to wait between page retrievals from /repositories endpoint')

@click.option('--min-rate-limit', '-l', type=int, default=30, help='Minimum remaining rate limit on API under which the crawl is interrupted')

@click.option('--batch-size', '-n', type=int, default=3000, help='Number of pages  should (roughly) be processed before writing results to disk')

@click.option('--crawldir', '-d', help='Path to directory in which crawl results should be written')

def crawl_handler(start_id: str, max_id: int, interval: float, min_rate_limit: int, batch_size: int, crawldir: str) -> None:
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
    next_id = nextid(crawldir)
    current_max = max(start_id, next_id)
    while current_max < max_id:
        result = crawl(
            current_max,
            min(current_max + batch_size, max_id),
            interval,
            min_rate_limit,
        )
        outfile = os.path.join(crawldir, f'{current_max}.json')
        with open(outfile, 'w') as ofp:
            json.dump(result, ofp)

        if len(result['data']) == 0:
            break
        current_max = result['data'][-1]['id']

        if result['ending_rate_limit'] < min_rate_limit:
            break

def ordered_crawl(crawldir: str) -> List[Tuple[str, int]]:
    """
    Returns the contents of the given crawl directory ordered by their start id (in ascending order)

    Args:
    crawldir
        Directory containing the results of an allrepos crawl

    Returns: List of crawl results in the given crawldir, ordered by the start ID for the crawl
    step they represent. Returns the start_id of each result file as the second coordinate of each
    tuple in the return list.
    """
    result_files = glob.glob(os.path.join(crawldir, '*.json'))
    if not result_files:
        return []
    indexed_result_files = [
        (
            rfile,
            int(os.path.basename(rfile).split('.')[0])
        ) for rfile in result_files
    ]
    return sorted(indexed_result_files, key=lambda p: p[1])


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


@click.command()
@click.option('--crawldir', '-d', help='Path to directory in which crawl results should be written')
def nextid_handler(crawldir: str) -> None:
    """
    Prints ID of most recent repository crawled and written to the crawldir parsed into the given
    argparse args object.

    Args:
    args
        Namespace containing arguments parsed from command line

    Returns: None. Prints most recent repository ID to screen.
    """
    print(nextid(crawldir))

def validate(result_range: List[Tuple[str, int]]) -> List[Tuple[int, int]]:
    """
    Given a directory containing only JSON files produced by an allrepos crawl, this function
    validates that there are no holes in the crawled data

    Args:
    result_range
        Contiguous list of results as returned by an ordered_crawl

    Returns: List of (start_id, max_id) pairs that are missing from the given range
    """
    if len(result_range) <= 1:
        return []

    missing_ranges: List[Tuple[int, int]] = []

    for i, pair in enumerate(result_range[:-1]):
        result_file, this_id = pair
        with open(result_file, 'r') as ifp:
            result = json.load(ifp)
        _, next_id = result_range[i+1]
        if not result.get('data'):
            missing_ranges.append((this_id, next_id))
            continue
        max_id = result['data'][-1].get('id', -1)
        if max_id != next_id:
            missing_ranges.append((max_id, next_id))

    return missing_ranges




@click.command()
@click.option( '--crawldir', '-d',  help='Path to directory in which crawl results should be written')
@click.option('--num-processes', '-p', type=int, default=1, help='Number of processes to use when performing validation')
@click.option('--outfile', '-o', help='Path to file into which validation output should be written')
def validate_handler(crawldir: str, num_processes: int, outfile: str) -> None:
    """
    Prints ID of most recent repository crawled and written to the crawldir parsed into the given
    argparse args object.

    Args:
    args
        Namespace containing arguments parsed from command line

    Returns: None. Prints most recent repository ID to screen.
    """
    ofp = sys.stdout
    if outfile is not None:
        ofp = open(outfile, 'w')
    invalid = []

    result_files = ordered_crawl(crawldir)
    if len(result_files) > 1:
        concurrency = num_processes
        if concurrency > len(result_files) - 1:
            concurrency = len(result_files) - 1
        worker_pool = multiprocessing.Pool(concurrency)
        segment_size = int((len(result_files) - 1)/concurrency) + 1
        ranges = [result_files[i*segment_size:(i+1)*segment_size + 1] for i in range(concurrency)]
        invalid = [range for results in worker_pool.map(validate, ranges) for range in results]

    json.dump(invalid, ofp)
    if outfile is not None:
        ofp.close()


def sample(crawl_batches: List[str], choose_probability: float) -> Iterator[Dict[str, Any]]:
    """
    Given a directory containing only JSON files produced by an allrepos crawl, this generator
    yields the next sample.

    NOTE: Not what I expected, but much faster than the following command:
    $ cat <crawldir>/*.json | jq -rc ".data[]" | perl -n -e 'print if (rand() < .01)' >outfile.jsonl

    perl bit comes from here:
    https://stackoverflow.com/questions/692312/randomly-pick-lines-from-a-file-without-slurping-it-with-unix
    (It's such a nice sampling trick.)

    NOTE: Useful command when testing sample rate:
    $ ls -1 <crawldir> | xargs -I{} jq ".data | length" <crawldir>/{} | awk '{s+=$1} END {print s}'
    Takes some time to run, though.

    Args:
    crawldir
        Output directory for an allrepos crawl
    choose_probability
        Probability with which any single document is chosen for the sample

    Returns: JSON array containing the sampled repositories
    """
    assert 0 <= choose_probability <= 1

    for batch in tqdm(crawl_batches, desc='batch'):
        with open(batch, 'r') as ifp:
            result = json.load(ifp)
        for repository in tqdm(result['data'], desc='repository', leave=False):
            if random.random() < choose_probability:
                yield repository

@click.command()
@click.option('--crawldir', '-d', help='Path to directory in which crawl results should be written')
@click.option('--outfile', '-o', type=click.File('w'), default=sys.stdout, help='Path to file to which samples should be written (default: stdout)')
@click.option('--probability', '-p', type=float, help='Probability with which a repository in the crawl directory should be chosen')
@click.option('--from-id', default=0,
    help=(
        'GitHub ID to begin sampling from (default: 0). Could have non-intuitive behavior '
        'since it uses the id on the crawl batch file, and not the id on the repos themselves. '
        'Uses the batch whose starting GitHub ID is the smallest one greater than --from-id.'
    )
)
@click.option('--to-id', type=int, default=None, help='GitHub ID to end sampling at (default: None)') # exception may
def sample_handler(crawldir: str, outfile: click.File('w'), probability: float, from_id: int,  to_id: str) -> None:
    """
    Writes repositories sampled from a crawl directory to an output file in JSON lines format

    Args:
    args
        Namespace containing arguments parsed from command line

    Returns: None
    """
    # Validator for files containing crawl result batches
    def is_valid(batch_item):
        _, start_id = batch_item
        if start_id < from_id:
            return False
        if to_id is not None and start_id > to_id:
            return False
        return True

    with outfile as ofp:
        ordered_batches = ordered_crawl(crawldir)
        valid_batches = [batch[0] for batch in ordered_batches if is_valid(batch)]
        samples = sample(valid_batches, probability)
        for repository in samples:
            print(json.dumps(repository), file=ofp)
