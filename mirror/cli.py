import click
from .github.allrepos import crawl_handler as crawl_populator
from .github.allrepos import nextid_handler as nextid_populator
from .github.allrepos import sample_handler as sample_populator
from .github.allrepos import validate_handler as validate_populator
from .github.commits import commits
from .github.search import popular_repos
from .github.clone_repos import clone_repos
from .github.sync import handler as sync_populator
from .github.licenses import licenses_handler as licenses_populator


@click.group()
def github() -> None:
    """'mirror - Tools for software project analysis'"""
    pass

github.add_command(crawl_populator, name="crawl")
github.add_command(nextid_populator, name="nextid")
github.add_command(sample_populator, name="sample")
github.add_command(validate_populator, name="validate")
github.add_command(popular_repos, name="search")
github.add_command(clone_repos, name="clone")

github.add_command(commits, name="commits")

cli = click.CommandCollection(sources=[github])

if __name__ == '__main__':
    cli()
