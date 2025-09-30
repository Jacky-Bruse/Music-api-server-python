import time

from utils import log
from .constants import (
    Source_Quality_Map,
    sourceExpirationTime,
    sourceNameTranslate,
    QualityNameTranslate,
)
from server.config import config, cache as cacheM
from server.models import Song, SongInfo, UrlResponse
from server.exceptions import getLyricFailed, getSongInfoFailed, getUrlFailed

from . import plat
from . import refresh
from . import url
from . import lyric
from . import info

logger = log.createLogger("Music API Handler")
CACHE_ENABLE = config.read("cache.enable")


def _build_error_message(exc: Exception, default: str) -> str:
    message = str(exc).strip()
    return message if message else default


def require(module: str):
    index = 0
    module_array = module.split(".")
    for m in module_array:
        if index == 0:
            _module = __import__(m)
            index += 1
        else:
            _module = getattr(_module, m)
            index += 1
    return _module


async def _url(source: str, songId: str, quality: str) -> dict:
    if quality == "flac24bit":
        quality = "hires"

    if quality not in Source_Quality_Map[source]:
        return {
            "code": 400,
            "message": "参数quality不正确, 此平台支持音质在下面",
            "support_quality": Source_Quality_Map[source],
        }

    if CACHE_ENABLE:
        try:
            cache = cacheM.get("urls", f"{source}_{songId}_{quality}")
            if cache:
                logger.info(
                    f"使用缓存的{sourceNameTranslate[source]}_{songId}_{QualityNameTranslate[quality]}数据, URL: {cache['url']['url']}"
                )

                result = UrlResponse(**cache["url"])

                return {
                    "code": 200,
                    "message": "成功",
                    "url": result.url,
                    "ekey": result.ekey,
                    "quality": QualityNameTranslate[result.quality],
                    "cache": {
                        "cache": True,
                        "canExpire": cache["expire"],
                        "expireAt": (
                            time.strftime(
                                "%Y-%m-%d %H:%M:%S", time.localtime(cache["time"])
                            )
                            if cache["expire"]
                            else None
                        ),
                    },
                }
        except Exception as e:
            logger.warning(
                f"读取缓存{sourceNameTranslate[source]}_{songId}_{QualityNameTranslate[quality]}失败: {e}, 将重新请求"
            )

    try:
        func = require(f"modules.url.{source}.getUrl")
    except (ImportError, AttributeError) as e:
        logger.error(f"模块加载失败 modules.url.{source}.getUrl: {e}")
        return {
            "code": 404,
            "message": "未知的源或不支持的方法",
        }

    try:
        result: UrlResponse | Song = await func(songId, quality)
        if source == "mg":
            result: UrlResponse = result.url

        logger.info(
            f"获取{sourceNameTranslate[source]}_{songId}_{QualityNameTranslate[quality]}成功, URL: {result.url}"
        )
        canExpire = sourceExpirationTime[source]["expire"]
        expireTime = int(sourceExpirationTime[source]["time"] * 0.75)
        expireAt = int(expireTime + time.time())
        if CACHE_ENABLE:
            cacheM.set(
                "urls",
                f"{source}_{songId}_{quality}",
                {
                    "time": expireAt,
                    "expire": canExpire,
                    "url": result.__dict__,
                },
                expireTime if canExpire else None,
            )
            logger.info(
                f"缓存已更新: {sourceNameTranslate[source]}_{songId}_{QualityNameTranslate[quality]}, URL: {result.url}, Expire: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expireAt))}"
            )

        return {
            "code": 200,
            "message": "成功",
            "url": result.url,
            "ekey": result.ekey,
            "quality": QualityNameTranslate[result.quality],
            "cache": {
                "cache": False,
                "canExpire": canExpire,
                "expireAt": (
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expireAt))
                    if canExpire
                    else None
                ),
            },
        }
    except getUrlFailed as e:
        logger.error(
            f"获取{sourceNameTranslate[source]}_{songId}_{QualityNameTranslate[quality]}失败，原因：{e}"
        )
        return {
            "code": 500,
            "message": _build_error_message(e, "获取URL失败"),
        }


async def _info(source, songId):
    if CACHE_ENABLE:
        try:
            cache = cacheM.get("info", f"{source}_{songId}")
            if cache:
                logger.debug(f"使用缓存的{sourceNameTranslate[source]}_{songId}歌曲信息")
                return {"code": 200, "message": "成功", "data": cache["data"]}
        except Exception as e:
            logger.warning(f"读取缓存{sourceNameTranslate[source]}_{songId}信息失败: {e}, 将重新请求")

    try:
        func = require("modules.info." + source + ".getMusicInfo")
    except (ImportError, AttributeError) as e:
        logger.error(f"模块加载失败 modules.info.{source}.getMusicInfo: {e}")
        return {
            "code": 404,
            "message": "未知的源或不支持的方法",
        }

    try:
        if source == "kg":
            result, _ = await func(songId)
        else:
            result: SongInfo = await func(songId)
        expireTime = 86400 * 3
        expireAt = int(time.time() + expireTime)
        if CACHE_ENABLE:
            cacheM.set(
                "info",
                f"{source}_{songId}",
                {
                    "data": result.__dict__,
                    "time": expireAt,
                    "expire": True,
                },
                expireTime,
            )
            logger.debug(f"缓存已更新：{source}_{songId}")
        return {"code": 200, "message": "成功", "data": result.__dict__}
    except getSongInfoFailed as e:
        return {
            "code": 500,
            "message": _build_error_message(e, "获取歌曲信息失败"),
        }


async def _lyric(source, songId):
    if CACHE_ENABLE:
        try:
            cache = cacheM.get("lyric", f"{source}_{songId}")
            if cache:
                logger.debug(f"使用缓存的{sourceNameTranslate[source]}_{songId}歌词")
                return {"code": 200, "message": "success", "data": cache["data"]}
        except Exception as e:
            logger.warning(f"读取缓存{sourceNameTranslate[source]}_{songId}歌词失败: {e}, 将重新请求")

    if source == "tx":
        try:
            songinfo = await info.tx.getMusicInfo(songId)
            songId = songinfo.songId
        except getSongInfoFailed as e:
            return {
                "code": 500,
                "message": _build_error_message(e, "获取歌曲信息失败"),
            }

    if source == "mg":
        try:
            song: Song = await url.mg.getUrl(songId, "128k")
            result = song.info.lyric
            expireTime = 86400 * 3
            expireAt = int(time.time() + expireTime)
            cacheM.set(
                "lyric",
                f"{source}_{songId}",
                {
                    "data": result,
                    "time": expireAt,
                    "expire": True,
                },
                expireTime,
            )
            logger.debug(f"缓存已更新：{source}_{songId}, lyric: {result}")
            return {"code": 200, "message": "成功", "data": result}
        except getLyricFailed as e:
            return {
                "code": 500,
                "message": _build_error_message(e, "获取歌词失败"),
            }

    try:
        func = require("modules.lyric." + source + ".getLyric")
    except (ImportError, AttributeError) as e:
        logger.error(f"模块加载失败 modules.lyric.{source}.getLyric: {e}")
        return {
            "code": 404,
            "message": "未知的源或不支持的方法",
        }

    try:
        result = await func(songId)
        expireTime = 86400 * 3
        expireAt = int(time.time() + expireTime)
        if CACHE_ENABLE:
            cacheM.set(
                "lyric",
                f"{source}_{songId}",
                {
                    "data": result,
                    "time": expireAt,
                    "expire": True,
                },
                expireTime,
            )
            logger.debug(f"缓存已更新：{source}_{songId}, lyric: {result}")
        return {"code": 200, "message": "成功", "data": result}
    except getLyricFailed as e:
        return {
            "code": 500,
            "message": _build_error_message(e, "获取歌词失败"),
        }
