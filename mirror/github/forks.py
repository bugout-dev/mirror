import logging
import time
from typing import List

from . import calls
from .data import RepositoryFork

logger = logging.getLogger(__name__)

interval = 1


def get_repository_forks(owner: str, repo: str) -> List[RepositoryFork]:
    """
    Parse repository forks and return organized pydantic data.
    """
    forks: List[RepositoryFork] = []

    page = 1
    while True:
        try:
            time.sleep(interval)
            forks_raw = calls.fetch_repository_forks(
                owner=owner, repo=repo, per_page=100, page=page
            )
            for fork_raw in forks_raw:
                forks.append(
                    RepositoryFork(
                        name=fork_raw.get("name"),
                        full_name=fork_raw.get("full_name"),
                        owner=fork_raw.get("owner").get("login")
                        if fork_raw.get("owner") is not None
                        else None,
                        html_url=fork_raw.get("html_url"),
                        forks_count=fork_raw.get("created_at"),
                        created_at=fork_raw.get("updated_at"),
                        updated_at=fork_raw.get("forks_count"),
                    )
                )
            if len(forks_raw) == 0:
                logger.info(
                    f"Parsing of repository forks finished, total number of forks: {len(forks)}"
                )
                break
        except Exception:
            logger.error(
                f"Unexpected error occurred due parsing repository forks"
            )
            break
        page += 1

    return forks
