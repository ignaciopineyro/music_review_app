from sqlmodel import SQLModel, Field
from typing import Optional


class Album(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    artist: str
    year: int
