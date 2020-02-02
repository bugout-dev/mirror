"""
Collect metadata for all GitHub repositories readable to the given token.

Support checkpointing against a small state object - the integer ID of the last repository seen.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, TextIO

import requests

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

def populator(parser: argparse.ArgumentParser) -> None:
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
        '--outfile',
        '-o',
        required=False,
        help='Path to file at which crawl results should be written',
    )

    parser.set_defaults(func=allrepos_handler)

def allrepos_handler(args: argparse.Namespace) -> None:
    file_handle: TextIO = sys.stdout
    if args.outfile is not None:
        file_handle = open(args.outfile, 'w')

    try:
        result = crawl(args.start_id, args.max_id, args.interval, args.min_rate_limit)
        json.dump(result, file_handle)
    finally:
        if args.outfile is not None:
            file_handle.close()
