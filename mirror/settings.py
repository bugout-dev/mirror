import os
import uuid
from typing import Optional
from importlib.machinery import SourceFileLoader

MODULE_NAME = "mirror"

module = SourceFileLoader(
    MODULE_NAME, os.path.join(MODULE_NAME, "__init__.py")
).load_module()

module_version = module.__version__

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
LANGUAGES_DIR = os.environ.get("LANGUAGES_DIR")
MIRROR_CRAWL_INTERVAL_SECONDS = os.environ.get("MIRROR_CRAWL_INTERVAL_SECONDS")
MIRROR_CRAWL_MIN_RATE_LIMIT = os.environ.get("MIRROR_CRAWL_MIN_RATE_LIMIT")
MIRROR_CRAWL_BATCH_SIZE = os.environ.get("MIRROR_CRAWL_BATCH_SIZE")
MIRROR_CRAWL_DIR = os.environ.get("MIRROR_CRAWL_DIR")
