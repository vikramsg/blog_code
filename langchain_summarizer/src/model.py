from typing import Dict

from pydantic import BaseModel


class Page(BaseModel):
    pageid: int
    title: str
    extract: str


class WikiPageQuery(BaseModel):
    pages: Dict[str, Page]


class WikiPageResponse(BaseModel):
    batchcomplete: str
    query: WikiPageQuery
