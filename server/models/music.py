from typing import Optional

from pydantic import BaseModel


class UrlResponse(BaseModel):
    url: str
    quality: str
    ekey: Optional[str] = None


class TXSpecial(BaseModel):
    songMid: Optional[str] = None
    mediaMid: Optional[str] = None
    albumMid: Optional[str] = None


class KGSpecial(BaseModel):
    hash: Optional[str] = None
    albumAudioId: Optional[str | int] = None


class Lyric(BaseModel):
    lyric: str
    trans: Optional[str] = None
    roma: Optional[str] = None
    chase: Optional[str] = None


class SongInfo(BaseModel):
    songId: str | int
    songName: str
    artistName: str
    albumName: Optional[str] = None
    albumId: Optional[str | int] = None
    duration: Optional[str] = None
    coverUrl: Optional[str] = None
    kg: Optional[KGSpecial] = None
    qq: Optional[TXSpecial] = None
