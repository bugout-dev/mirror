"""
CLI for `mirror github`
"""

import argparse
import json
import sys
from typing import TextIO

from . import allrepos
from ..populate import populate_cli

subcommand = 'github'

def populator(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers()

    allrepos_parser = subparsers.add_parser('allrepos')
    allrepos_parser.add_argument(
        '--start-id',
        '-s',
        type=int,
        default=0,
        help='Last ID seen in GitHub all repos crawl; current crawl will start from its successor',
    )
    allrepos_parser.add_argument(
        '--max-id',
        '-m',
        type=int,
        default=100000000,
        help='Crawl should extend to this idea (and no more than one page further)',
    )
    allrepos_parser.add_argument(
        '--interval',
        '-t',
        type=float,
        default=1.0,
        help='Number of seconds to wait between page retrievals from /repositories endpoint',
    )
    allrepos_parser.add_argument(
        '--min-rate-limit',
        '-l',
        type=int,
        default=30,
        help='Minimum remaining rate limit on API under which the crawl is interrupted',
    )
    allrepos_parser.add_argument(
        '--outfile',
        '-o',
        required=False,
        help='Path to file at which crawl results should be written',
    )

    def allrepos_handler(args: argparse.Namespace) -> None:
        file_handle: TextIO = sys.stdout
        if args.outfile is not None:
            file_handle = open(args.outfile, 'w')

        try:
            result = allrepos.crawl(args.start_id, args.max_id, args.interval, args.min_rate_limit)
            json.dump(result, file_handle)
        finally:
            if args.outfile is not None:
                file_handle.close()

    allrepos_parser.set_defaults(func=allrepos_handler)
