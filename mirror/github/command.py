"""
CLI for `mirror github`
"""

import argparse
from typing import Callable, Dict

from . import allrepos, licenses, sync
from ..populate import populate_cli

subcommand = 'github'

SUBCOMMAND_POPULATORS: Dict[str, Callable[[argparse.ArgumentParser], None]] = {
    'crawl': allrepos.crawl_populator,
    'nextid': allrepos.nextid_populator,
    'sample': allrepos.sample_populator,
    'validate': allrepos.validate_populator,
    'sync': sync.populator,
    licenses.subcommand: licenses.populator,
}

def populator(parser: argparse.ArgumentParser) -> None:
    populate_cli(parser, SUBCOMMAND_POPULATORS)
