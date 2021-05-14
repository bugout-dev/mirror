import os

from . import __version__

MIRROR_VERSION = __version__

DATETIME_HEADER = "Date"

REPOSITORIES_URL = "https://api.github.com/repositories"
REMAINING_RATELIMIT_HEADER = "X-RateLimit-Remaining"
RESET_RATELIMIT_HEADER = "X-RateLimit-Reset"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if GITHUB_TOKEN is None:
    raise ValueError("GITHUB_TOKEN environment variable must be set")

CLONE_DIR = os.environ.get("CLONE_DIR")
if CLONE_DIR is None:
    raise ValueError("CLONE_DIR environment variable must be set")

MIRROR_CRAWL_INTERVAL_SECONDS = os.environ.get("MIRROR_CRAWL_INTERVAL_SECONDS")
MIRROR_CRAWL_MIN_RATE_LIMIT = os.environ.get("MIRROR_CRAWL_MIN_RATE_LIMIT")
MIRROR_CRAWL_BATCH_SIZE = os.environ.get("MIRROR_CRAWL_BATCH_SIZE")
MIRROR_CRAWL_DIR = os.environ.get("MIRROR_CRAWL_DIR")
