import random

from server.config import config
from server.exceptions import FailedException
from server.models.music import UrlResponse
from utils.encode import json
from utils.platform.wy import eEncrypt, QMap
from utils.server.http import send_http_request


async def getUrl(songId: str, quality: str) -> UrlResponse:
    try:
        path = "/api/song/enhance/player/url/v1"
        url = "https://interface.music.163.com/eapi/song/enhance/player/url/v1"
        params = {
            "ids": json.dumps([songId]),
            "level": QMap["qualityMap"][quality],
            "encodeType": "mp3",
        }

        req = await send_http_request(
            url,
            {
                "method": "POST",
                "headers": {
                    "User-Agent": "NeteaseMusic/9.3.0.250516233250(9003000);Dalvik/2.1.0 (Linux; U; Android 12; ABR-AL80 Build/9b35a01.0)",
                    "Cookie": "NMTID=00OtHNvqMP4xx8E1UPBiI7sPBtdEkYAAAGYwqmkDQ;WEVNSM=1.0.0;os=pc;deviceId=6873B8B560CC9504C04C54323CDADF75B16DC4B1E89C257D111A;osver=Microsoft-Windows-11--build-22631-64bit;appver=3.1.16.204365;clientSign=E8:9C:25:7D:11:1A@@@YVJ4LKJA@@@@@@c71948d7c7e030782828c655db9758664f8db47b31bf0822bf64ad5946c79c73;channel=netease;mode=System Product Name;JSESSIONID-WYYY=5Hg8m%2BdujO5XQzfFDsXGR%2BMzzEQ5PWx94z0G4fBTnt%2BaTXudFVbC9cn%2B5Bzii0dQX%2BjwMxdubid7%5Cva6SYsMu4qTct55FIbK4z2NCy%2B%2F3QBd4ln9huh40i0KVHgA%2BoU5OoAmHykucpR3xu6RWNnhXUny9OHAaGFfHFBV6WY%2BS%2B%2FWK5WF%3A1755614540342;_iuqxldmzr_=33;_ntes_nnid=3c28c8c0d83a91f6fba69ba5907027a1,1755612740378;_ntes_nuid=3c28c8c0d83a91f6fba69ba5907027a1;__csrf=c9a7872d1633940441ff4e9fcb2fd721;ntes_kaola_ad=1;WNMCID=jwyezp.1755612752936.01.0;MUSIC_U="
                              + random.choice(config.get("modules.platform.wy.users")),
                },
                "form": eEncrypt(path, params),
            },
        )

        body = req.json()

        if not body["data"] or (not body["data"][0]["url"]):
            raise FailedException("获取URL失败: 未返回URL")

        data = body["data"][0]
        purl = str(data["url"])

        if data["level"] not in QMap["qualityMapReverse"]:
            raise FailedException("未知的音质")

        return UrlResponse(
            url=purl.split("?")[0],
            quality=QMap["qualityMapReverse"][data["level"]],
        )
    except Exception as e:
        raise FailedException(e)
