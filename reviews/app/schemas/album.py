from sqlmodel import SQLModel


class AlbumCreate(SQLModel):
    title: str
    artist: str
    year: int


class AlbumRead(SQLModel):
    id: int
    title: str
    artist: str
    year: int
