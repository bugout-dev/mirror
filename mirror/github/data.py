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




class IssuesPublic(MyBaseModel):
    body: Optional[str] = None
    title:  Optional[str] = None
    comments_url: Optional[str] = None
    comments: Optional[int] = None
    html_url: Optional[str] = None
    state: Optional[str] = None
    number: Optional[int] = None
    author_association: Optional[str] = None
    url: Optional[str] = None
    repository_url: Optional[str] = None
    labels_url: Optional[str] = None
    events_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

