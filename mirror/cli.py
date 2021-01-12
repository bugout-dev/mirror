# import argparse
# from typing import Callable, Dict

# from .populate import populate_cli
# from .github import command as github



#     'crawl': allrepos.crawl_populator,
#     'nextid': allrepos.nextid_populator,
#     'sample': allrepos.sample_populator,
#     'validate': allrepos.validate_populator,
#     'sync': sync.populator,
#     licenses.subcommand: licenses.populator,







import click
from .github.allrepos import crawl_handler as crawl_populator
from .github.allrepos import nextid_handler as nextid_populator
from .github.allrepos import sample_handler as sample_populator
from .github.allrepos import validate_handler as validate_populator
from .github.sync import handler as sync_populator
from .github.licenses import licenses_handler as licenses_populator

# SUBCOMMAND_POPULATORS: Dict[str, Callable[[argparse.ArgumentParser], None]] = {
#     github.subcommand: github.populator,
# }
@click.group()
def github() -> None:
    """'mirror - Tools for software project analysis'"""
    pass
    # parser = argparse.ArgumentParser('mirror - Tools for software project analysis')
    # populate_cli(parser, SUBCOMMAND_POPULATORS)

    # args = parser.parse_args()
    # args.func(args)

github.add_command(crawl_populator, name="crawl")
github.add_command(nextid_populator, name="nextid")
github.add_command(sample_populator, name="sample")
github.add_command(validate_populator, name="validate")

cli = click.CommandCollection(sources=[github])

if __name__ == '__main__':
    cli()
