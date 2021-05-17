# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
from typing import List, Optional

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


class RepositoryFork(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    owner: Optional[str] = None
    html_url: Optional[str] = None
    forks_count: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RepositoryForksList(BaseModel):
    owner: str
    repo: str
    forks: List[RepositoryFork] = Field(default_factory=set)
