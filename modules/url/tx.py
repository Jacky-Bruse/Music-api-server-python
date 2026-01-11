import random

from modules.constants import translateStrOrInt
from modules.info.tx import getMusicInfo
from server.config import config
from server.exceptions import FailedException
from server.models.music import UrlResponse
from utils.platform.tx import build_comm
from utils.platform.tx import sign_request

guidList = [
    "Feixiao",
    "Tingyun",
    "Yingxing",
    "History",
    "Chinese",
    "English",
    "Geography",
]

qualityMap = {
    "128k": {
        "e": ".mp3",
        "h": "M500",
    },
    "320k": {
        "e": ".mp3",
        "h": "M800",
    },
    "flac": {
        "e": ".flac",
        "h": "F000",
    },
    "hires": {
        "e": ".flac",
        "h": "RS01",
    },
    "atmos": {
        "e": ".flac",
        "h": "Q000",
    },
    "atmos_plus": {
        "e": ".flac",
        "h": "Q001",
    },
    "master": {
        "e": ".flac",
        "h": "AI00",
    },
    "nac": {
        "e": ".nac",
        "h": "TL01",
    },
    "dts": {
        "e": ".mp4",
        "h": "DT03",
    },
}
encryptMap = {
    "128k": {
        "e": ".mgg",
        "h": "O6M0",
    },
    "320k": {
        "e": ".mgg",
        "h": "O8M0",
    },
    "flac": {
        "e": ".mflac",
        "h": "F0M0",
    },
    "hires": {
        "e": ".mflac",
        "h": "RSM1",
    },
    "atmos": {
        "e": ".mflac",
        "h": "Q0M0",
    },
    "atmos_plus": {
        "e": ".mflac",
        "h": "Q0M1",
    },
    "master": {
        "e": ".mflac",
        "h": "AIM0",
    },
    "nac": {
        "e": ".mnac",
        "h": "TLM1",
    },
    "dts": {
        "e": ".mmp4",
        "h": "DTM3",
    },
}


async def getUrl(songId: str | int, quality: str) -> UrlResponse:
    try:
        info = await getMusicInfo(songId)

        songId = info.qq.songMid
        strMediaMid = info.qq.mediaMid

        user_info = config.get("modules.platform.tx.users")
        if quality not in ["128k", "320k", "flac", "hires"]:
            user_info = random.choice(
                [user for user in user_info if user.get("vipType") == "svip"]
            )
        else:
            user_info = random.choice(user_info)

        comm = await build_comm(user_info)
        guid = random.choice(guidList)
        resp = await sign_request(
            {
                "comm": comm,
                "request": {
                    "module": "music.vkey.GetVkey",
                    "method": "UrlGetVkey",
                    "param": {
                        "guid": guid,
                        "uin": user_info["uin"],
                        "downloadfrom": 1,
                        "ctx": 1,
                        "referer": "y.qq.com",
                        "scene": 0,
                        "songtype": [1],
                        "songmid": [songId],
                        "filename": [
                            f"{qualityMap[quality]['h']}{strMediaMid}{qualityMap[quality]['e']}"
                        ],
                    },
                },
            }
        )

        body = resp.json()
        data = body["request"]["data"]["midurlinfo"][0]

        purl = str(data["purl"])
        if not purl:
            raise FailedException(translateStrOrInt(body["request"]["code"]))

        cdnaddr = random.choice(config.get("modules.platform.tx.cdn_list"))
        url = cdnaddr + purl

        return UrlResponse(
            url=url,
            quality=quality,
        )
    except Exception as e:
        raise FailedException(e)
