"""
CLI for `mirror github`
"""

import argparse
from typing import Callable, Dict

from . import allrepos, licenses
from ..populate import populate_cli

subcommand = 'github'

SUBCOMMAND_POPULATORS: Dict[str, Callable[[argparse.ArgumentParser], None]] = {
    allrepos.subcommand: allrepos.populator,
    licenses.subcommand: licenses.populator,
}

def populator(parser: argparse.ArgumentParser) -> None:
    populate_cli(parser, SUBCOMMAND_POPULATORS)
