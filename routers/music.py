from fastapi import Request
from fastapi.routing import APIRouter

import modules
from utils.server.response import handleResponse

router = APIRouter()


@router.get("/url")
async def handle_song_url(request: Request, source: str, songId: str, quality: str):
    if source == "kg":
        songId = songId.lower()

    result = await modules.url.getUrl(source, songId, quality)

    return handleResponse(result)


@router.get("/info")
async def handle_song_info(request: Request, source: str, songId: str):
    if source == "kg":
        songId = songId.lower()

    result = await modules.info.getSongInfo(source, songId)

    return handleResponse(result)


@router.get("/lyric")
async def handle_lyric(request: Request, source: str, songId: str):
    if source == "kg":
        songId = songId.lower()

    result = await modules.lyric.getLyric(source, songId)

    return handleResponse(result)
