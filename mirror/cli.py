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
from .github.sync import handler as sync_populator
from .github.licenses import licenses_handler as licenses_populator
from .data import stacktraces


@click.group()
def mirror() -> None:
    """'mirror - Tools for software project analysis'"""
    pass


@mirror.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
def version() -> None:
    click.echo(__version__)


@mirror.group("github")
def mirror_github() -> None:
    pass


mirror_github.add_command(crawl_populator, name="crawl")
mirror_github.add_command(nextid_populator, name="nextid")
mirror_github.add_command(sample_populator, name="sample")
mirror_github.add_command(validate_populator, name="validate")
mirror_github.add_command(popular_repos, name="search")
mirror_github.add_command(clone_repos, name="clone")
mirror_github.add_command(generate_datasets, name="generate_snippets")
mirror_github.add_command(commits, name="commits")


@mirror.group(
    "data",
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
def mirror_data() -> None:
    pass


mirror_data.add_command(stacktraces.handler, "stacktraces")


cli = click.CommandCollection(sources=[mirror])

if __name__ == "__main__":
    cli()
