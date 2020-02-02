import argparse
from typing import Callable, Dict

from .populate import populate_cli
from .github import command as github

SUBCOMMAND_POPULATORS: Dict[str, Callable[[argparse.ArgumentParser], None]] = {
    github.subcommand: github.populator,
}

def main() -> None:
    parser = argparse.ArgumentParser('mirror - Tools for software project analysis')
    populate_cli(parser, SUBCOMMAND_POPULATORS)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
