import random

from server.config import config
from server.exceptions import FailedException
from server.models.music import UrlResponse
from utils.server import http as request

tools = {
    "qualityMap": {
        "128k": "128kmp3",
        "320k": "320kmp3",
        "flac": "2000kflac",
        "hires": "4000kflac",
    },
    "qualityMapReverse": {
        128: "128k",
        320: "320k",
        2000: "flac",
        4000: "hires",
    },
    "extMap": {
        "128k": "mp3",
        "320k": "mp3",
        "flac": "flac",
        "hires": "flac",
    },
}


async def getUrl(songId: str | int, quality: str) -> UrlResponse:
    try:
        source = random.choice(config.get("modules.platform.kw.source_list"))

        params = {
            "user": "359307055300426",
            "source": source,
            "type": "convert_url_with_sign",
            "br": tools["qualityMap"][quality],
            "format": tools["extMap"][quality],
            "sig": "0",
            "rid": songId,
            "network": "WIFI",
            "f": "web",
        }

        params = "&".join([f"{k}={v}" for k, v in params.items()])

        target_url = f"https://mobi.kuwo.cn/mobi.s?{params}"

        req = await request.send_http_request(
            target_url,
            {
                "method": "GET",
                "headers": {"User-Agent": "okhttp/3.10.0"},
            },
        )

        if req.json()["code"] != 200:
            raise FailedException("网络请求错误")

        body = req.json()["data"]

        url = str(body["url"])
        bitrate = int(body["bitrate"])

        quality = (
            tools["qualityMapReverse"].get(bitrate)
            if tools["qualityMapReverse"].get(bitrate)
            else "128k"
        )

        return UrlResponse(
            url=url.split("?")[0],
            quality=quality,
        )
    except Exception as e:
        raise FailedException(e)
