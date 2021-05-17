"""
Processing requests to GitHub API.
"""
import logging
from typing import Any, Dict, List, Union

import requests

from ..settings import GITHUB_API_URL, GITHUB_API_REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class GitHubApiCallFailed(Exception):
    """
    Raised on actions that involve calls to GitHub API which are failed.
    """


def fetch_repository_forks(
    owner: str,
    repo: str,
    sort: str = "newest",
    per_page: int = 100,
    page: int = 1,
) -> List[Dict[str, Any]]:
    """
    Fetch forks for provided repository from GitHub.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/forks"
    headers = {"Accept": "application/vnd.github.v3+json"}
    params: Dict[str, Union[str, int]] = {
        "sort": sort,
        "per_page": per_page,
        "page": page,
    }
    try:
        r = requests.get(
            url, headers=headers, params=params, timeout=GITHUB_API_REQUEST_TIMEOUT
        )
        r.raise_for_status()
        response = r.json()
    except Exception as e:
        logger.error(repr(e))
        raise GitHubApiCallFailed("An error occurred due fetching forks via GitHub API")
    return response
