import click

from . import __version__
from .github.allrepos import crawl_handler as crawl_populator
from .github.allrepos import nextid_handler as nextid_populator
from .github.allrepos import sample_handler as sample_populator
from .github.allrepos import validate_handler as validate_populator
from .github.commits import commits
from .github.search import popular_repos
from .github.clone_repos import clone_repos
from .github.generate_snippets import generate_datasets


@click.group()
def mirror() -> None:
    """'mirror - Tools for software project analysis'"""
    pass


@mirror.command()
def version() -> None:
    click.echo(__version__)


mirror.add_command(crawl_populator, name="crawl")
mirror.add_command(nextid_populator, name="nextid")
mirror.add_command(sample_populator, name="sample")
mirror.add_command(validate_populator, name="validate")
mirror.add_command(popular_repos, name="search")
mirror.add_command(clone_repos, name="clone")
mirror.add_command(generate_datasets, name="generate_snippets")
mirror.add_command(commits, name="commits")

cli = click.CommandCollection(sources=[mirror])

if __name__ == "__main__":
    cli()
