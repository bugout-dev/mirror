import argparse
import logging
import time
from typing import List

from . import calls
from .data import RepositoryFork, RepositoryForksList

logger = logging.getLogger(__name__)


def get_repository_forks(
    owner: str, repo: str, sleep_interval: int = 1
) -> RepositoryForksList:
    """
    Parse repository forks and return organized pydantic data.
    """
    forks: List[RepositoryFork] = []

    page = 1
    while True:
        try:
            time.sleep(sleep_interval)
            forks_raw = calls.fetch_repository_forks(
                owner=owner, repo=repo, per_page=100, page=page
            )
            for fork_raw in forks_raw:
                owner_dict = fork_raw.get("owner")
                forks.append(
                    RepositoryFork(
                        name=fork_raw.get("name"),
                        full_name=fork_raw.get("full_name"),
                        owner=owner_dict.get("login")
                        if owner_dict is not None
                        else None,
                        html_url=fork_raw.get("html_url"),
                        forks_count=fork_raw.get("forks_count"),
                        created_at=fork_raw.get("created_at"),
                        updated_at=fork_raw.get("updated_at"),
                    )
                )
            if len(forks_raw) == 0:
                logger.info(
                    f"Parsing of repository forks finished, total number of forks: {len(forks)}"
                )
                break
        except Exception:
            logger.error(f"Unexpected error occurred due parsing repository forks")
            break
        page += 1

    return RepositoryForksList(owner=owner, repo=repo, forks=forks)


def cli_forks_handler(args: argparse.Namespace) -> None:
    forks = get_repository_forks(args.owner, args.repo)
    print(forks.json())


def mutate_argparser(subcommand) -> None:
    """
    Mutates the provided parser with GitHub Forks functionality.
    """
    parser_forks = subcommand.add_parser("forks", description="Mirror forks")
    parser_forks.add_argument(
        "-o", "--owner", required=True, help="GitHub username or organization name"
    )
    parser_forks.add_argument(
        "-r", "--repo", required=True, help="GitHub repository name"
    )
    parser_forks.set_defaults(func=cli_forks_handler)
