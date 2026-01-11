from server.exceptions import FailedException
from server.models.music import SongInfo, TXSpecial
from utils.platform import formatPlayTime, formatSinger
from utils.platform.tx import build_comm
from utils.platform.tx import sign_request


async def IdGetInfo(songid: int) -> SongInfo:
    comm = await build_comm()
    reqBody = {
        "comm": comm,
        "req": {
            "module": "music.trackInfo.UniformRuleCtrl",
            "method": "CgiGetTrackInfo",
            "param": {"types": [1], "ids": [songid], "ctx": 0},
        },
    }
    resp = await sign_request(reqBody)
    respBody = resp.json()

    if respBody["code"] != 0 or respBody["req"]["code"] != 0:
        raise FailedException("获取音乐信息失败")

    info = respBody["req"]["data"]["tracks"][0]

    return SongInfo(
        songId=info.get("id"),
        songName=(info.get("title", "") + info.get("subtitle", "")),
        artistName=formatSinger(info.get("singer", [])),
        albumName=(
                info.get("album", {}).get("title", "")
                + info.get("album", {}).get("subtitle", "")
        ),
        albumId=info.get("album", {}).get("id"),
        duration=(
            formatPlayTime(info.get("interval", 0))
            if info.get("interval") is not None
            else None
        ),
        qq=TXSpecial(
            songMid=info.get("mid"), albumMid=info.get("album", {}).get("mid"),
            mediaMid=info.get("file", {}).get("media_mid"),
        )
    )


async def MidGetInfo(mid: str) -> SongInfo:
    comm = await build_comm()
    reqBody = {
        "comm": comm,
        "req": {
            "method": "get_song_detail_yqq",
            "param": {"song_type": 0, "song_mid": mid},
            "module": "music.pf_song_detail_svr",
        },
    }

    resp = await sign_request(reqBody)
    respBody = resp.json()

    if respBody["code"] != 0 or respBody["req"]["code"] != 0:
        raise FailedException("获取音乐信息失败")

    info = respBody["req"]["data"]["track_info"]

    return SongInfo(
        songId=info.get("id"),
        songName=(info.get("title", "") + info.get("subtitle", "")),
        artistName=formatSinger(info.get("singer", [])),
        albumName=(
                info.get("album", {}).get("title", "")
                + info.get("album", {}).get("subtitle", "")
        ),
        albumId=info.get("album", {}).get("id"),
        duration=(
            formatPlayTime(info.get("interval", 0))
            if info.get("interval") is not None
            else None
        ),
        qq=TXSpecial(
            songMid=info.get("mid"),
            albumMid=info.get("album", {}).get("mid"),
            mediaMid=info.get("file", {}).get("media_mid"),
        )
    )


async def getMusicInfo(songId: str):
    if songId.isdigit() or isinstance(songId, int):
        return await IdGetInfo(int(songId))
    elif isinstance(songId, str):
        return await MidGetInfo(songId)
