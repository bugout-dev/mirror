import os
import uuid
from typing import Optional
from importlib.machinery import SourceFileLoader

from . import __version__

MODULE_NAME = "mirror"

module_version = __version__

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
LANGUAGES_DIR = os.environ.get("LANGUAGES_DIR")
MIRROR_CRAWL_INTERVAL_SECONDS = os.environ.get("MIRROR_CRAWL_INTERVAL_SECONDS")
MIRROR_CRAWL_MIN_RATE_LIMIT = os.environ.get("MIRROR_CRAWL_MIN_RATE_LIMIT")
MIRROR_CRAWL_BATCH_SIZE = os.environ.get("MIRROR_CRAWL_BATCH_SIZE")
MIRROR_CRAWL_DIR = os.environ.get("MIRROR_CRAWL_DIR")


github_license =  [
  {
    "key": "agpl-3.0",
    "name": "GNU Affero General Public License v3.0",
    "spdx_id": "AGPL-3.0",
    "url": "https://api.github.com/licenses/agpl-3.0",
    "node_id": "MDc6TGljZW5zZTE="
  },
  {
    "key": "apache-2.0",
    "name": "Apache License 2.0",
    "spdx_id": "Apache-2.0",
    "url": "https://api.github.com/licenses/apache-2.0",
    "node_id": "MDc6TGljZW5zZTI="
  },
  {
    "key": "bsd-2-clause",
    "name": "BSD 2-Clause \"Simplified\" License",
    "spdx_id": "BSD-2-Clause",
    "url": "https://api.github.com/licenses/bsd-2-clause",
    "node_id": "MDc6TGljZW5zZTQ="
  },
  {
    "key": "bsd-3-clause",
    "name": "BSD 3-Clause \"New\" or \"Revised\" License",
    "spdx_id": "BSD-3-Clause",
    "url": "https://api.github.com/licenses/bsd-3-clause",
    "node_id": "MDc6TGljZW5zZTU="
  },
  {
    "key": "bsl-1.0",
    "name": "Boost Software License 1.0",
    "spdx_id": "BSL-1.0",
    "url": "https://api.github.com/licenses/bsl-1.0",
    "node_id": "MDc6TGljZW5zZTI4"
  },
  {
    "key": "cc0-1.0",
    "name": "Creative Commons Zero v1.0 Universal",
    "spdx_id": "CC0-1.0",
    "url": "https://api.github.com/licenses/cc0-1.0",
    "node_id": "MDc6TGljZW5zZTY="
  },
  {
    "key": "epl-2.0",
    "name": "Eclipse Public License 2.0",
    "spdx_id": "EPL-2.0",
    "url": "https://api.github.com/licenses/epl-2.0",
    "node_id": "MDc6TGljZW5zZTMy"
  },
  {
    "key": "gpl-2.0",
    "name": "GNU General Public License v2.0",
    "spdx_id": "GPL-2.0",
    "url": "https://api.github.com/licenses/gpl-2.0",
    "node_id": "MDc6TGljZW5zZTg="
  },
  {
    "key": "gpl-3.0",
    "name": "GNU General Public License v3.0",
    "spdx_id": "GPL-3.0",
    "url": "https://api.github.com/licenses/gpl-3.0",
    "node_id": "MDc6TGljZW5zZTk="
  },
  {
    "key": "lgpl-2.1",
    "name": "GNU Lesser General Public License v2.1",
    "spdx_id": "LGPL-2.1",
    "url": "https://api.github.com/licenses/lgpl-2.1",
    "node_id": "MDc6TGljZW5zZTEx"
  },
  {
    "key": "mit",
    "name": "MIT License",
    "spdx_id": "MIT",
    "url": "https://api.github.com/licenses/mit",
    "node_id": "MDc6TGljZW5zZTEz"
  },
  {
    "key": "mpl-2.0",
    "name": "Mozilla Public License 2.0",
    "spdx_id": "MPL-2.0",
    "url": "https://api.github.com/licenses/mpl-2.0",
    "node_id": "MDc6TGljZW5zZTE0"
  },
  {
    "key": "unlicense",
    "name": "The Unlicense",
    "spdx_id": "Unlicense",
    "url": "https://api.github.com/licenses/unlicense",
    "node_id": "MDc6TGljZW5zZTE1"
  }
]
