from server.exceptions import FailedException
from server.models.music import SongInfo
from utils.encode import json
from utils.platform import formatPlayTime, formatSinger
from utils.platform.wy import eEncrypt
from utils.server.http import send_http_request


async def getMusicInfo(songId: str):
    path = "/api/v3/song/detail"
    url = "https://interface.music.163.com/eapi/v3/song/detail"
    params = {
        "c": [json.dumps({"id": songId})],
        "ids": [songId],
    }
    infoRequest = await send_http_request(
        url,
        {
            "method": "POST",
            "form": eEncrypt(path, params),
        },
    )

    infoBody = infoRequest.json()

    if infoBody["code"] != 200:
        raise FailedException("获取音乐信息失败")

    info = infoBody["songs"][0]

    return SongInfo(
        songId=info.get("id"),
        songName=info.get("name"),
        artistName=formatSinger(info.get("ar", [])),
        albumName=info.get("al", {}).get("name"),
        albumId=info.get("al", {}).get("id"),
        duration=(
            formatPlayTime(info.get("dt", 0) / 1000)
            if info.get("dt") is not None
            else None
        ),
        coverUrl=info.get("al", {}).get("picUrl"),
    )
