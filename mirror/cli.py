"""
The mirror command-line interface - gateway to all mirror functionality, accessible through
subcommands.
"""

import argparse
from typing import Callable, Dict

def generate_mirror_cli(
        subcommand_populators: Dict[str, Callable[[argparse.ArgumentParser], None]]
    ) -> argparse.ArgumentParser:
    """
    Generates an argparse.ArgumentParser which can be used to process mirror commands from the
    command line

    Args:
    subcommand_populators
        Dictionary whose keys are subcommands and whose values are functions which populate the
        subcommand parsers with their arguments (these should be exported by the submodule
        responsible for the functionality of the given subcommand)

    Returns: argparse.ArgumentParser object
    """
    parser = argparse.ArgumentParser('mirror - Tools for analyzing software projects')
    subcommand_parsers = parser.add_subparsers()

    for subcommand, populator in subcommand_populators.items():
        subparser = subcommand_parsers.add_parser(subcommand)
        populator(subparser)

    return parser

if __name__ == '__main__':
    args = parser.parse_args()
