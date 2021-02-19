"""
The mirror command-line interface - gateway to all mirror functionality, accessible through
subcommands.
"""

import argparse
from typing import Callable, Dict


def populate_cli(
    parser: argparse.ArgumentParser,
    subcommand_populators: Dict[str, Callable[[argparse.ArgumentParser], None]],
) -> None:
    """
    Populates an argparse.ArgumentParser instance with the given subcommands

    This function can be used by submodules

    Args:

    subcommand_populators
        Dictionary whose keys are subcommands and whose values are functions which populate the
        subcommand parsers with their arguments (these should be exported by the submodule
        responsible for the functionality of the given subcommand)

    Returns: argparse.ArgumentParser object
    """
    subcommand_parsers = parser.add_subparsers()

    for subcommand, populator in subcommand_populators.items():
        subparser = subcommand_parsers.add_parser(subcommand)
        populator(subparser)
