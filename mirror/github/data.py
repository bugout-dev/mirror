# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MyBaseModel(BaseModel):
    class Config:
        validate_assignment = True
        extra = "ignore"


class CommitPublic(MyBaseModel):
    sha: Optional[str] = None
    commit_url: Optional[str] = None
    html_url: Optional[str] = None
    author_html_url: Optional[str] = None
    committer_html_url: Optional[str] = None
