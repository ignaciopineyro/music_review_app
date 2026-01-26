from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db import get_session
from ..models.album import Album
from ..schemas.album import AlbumCreate, AlbumRead

router = APIRouter(prefix="/albums", tags=["albums"])


@router.post("/", response_model=AlbumRead)
async def create_album(data: AlbumCreate, session: AsyncSession = Depends(get_session)):
    album = Album(**data.model_dump())
    session.add(album)
    await session.commit()
    await session.refresh(album)

    return album


@router.get("/", response_model=list[AlbumRead])
async def list_albums(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Album))

    return result.all()


@router.get("/{album_id}", response_model=AlbumRead)
async def get_album(album_id: int, session: AsyncSession = Depends(get_session)):
    album = await session.get(Album, album_id)
    if not album:
        raise HTTPException(404, "Album not found")

    return album


@router.put("/{album_id}", response_model=AlbumRead)
async def update_album(
    album_id: int, data: AlbumCreate, session: AsyncSession = Depends(get_session)
):
    album = await session.get(Album, album_id)
    if not album:
        raise HTTPException(404, "Album not found")

    album.title = data.title
    album.artist = data.artist
    album.year = data.year

    session.add(album)
    await session.commit()
    await session.refresh(album)

    return album


@router.delete("/{album_id}")
async def delete_album(album_id: int, session: AsyncSession = Depends(get_session)):
    album = await session.get(Album, album_id)
    if not album:
        raise HTTPException(404, "Album not found")

    await session.delete(album)
    await session.commit()

    return {"message": "Album deleted successfully"}
