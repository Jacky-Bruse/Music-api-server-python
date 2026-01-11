import time
from importlib import import_module
from typing import Dict

from modules.constants import getExpireTime, translateStrOrInt
from server.cache import cache
from server.exceptions import FailedException
from server.models.music import UrlResponse
from server.statistics import stats_manager
from utils.server import log
from . import kg
from . import kw
from . import tx
from . import wy

logger = log.createLogger("URL Module")


def require(module: str):
    try:
        parts = module.split(".")
        mod = import_module(parts[0])
        for part in parts[1:]:
            mod = getattr(mod, part)
        return mod
    except (ImportError, ValueError, AttributeError):
        raise ImportError("未知的源/不支持的方法", name=module)


async def getUrl(source: str, songId: str | int, quality: str) -> Dict:
    if quality == "flac24bit":
        quality = "hires"

    trans_base = f"{translateStrOrInt(source)}_{songId}_{translateStrOrInt(quality)}"

    try:
        cache_key = f"{source}_{songId}_{quality}"
        cache_result = cache.get("url", cache_key)

        if cache_result:
            result = UrlResponse(**cache_result["url"])
            logger.info(f"使用缓存的url_{trans_base}")
            await stats_manager.increment(source, "url", True)
            return {
                "code": 200,
                "message": "成功",
                "url": result.url}

        func = require(f"modules.url.{source}.getUrl")
        result: UrlResponse = await func(songId, quality)

        logger.info(f"获取url_{trans_base}成功, URL: {result.url}")

        expireTime = getExpireTime(source)
        canExpire = expireTime != 0
        expireTime = int(expireTime * 0.75)
        expireAt = int(expireTime + time.time())

        cache.set(
            "url",
            cache_key,
            {
                "time": expireAt,
                "expire": canExpire,
                "url": result.__dict__,
            },
            expireTime if canExpire else None,
        )
        logger.debug(f"缓存已更新: url_{trans_base}")

        await stats_manager.increment(source, "url", True)
        return {
            "code": 200,
            "message": "成功",
            "url": result.url
        }

    except (FailedException, ImportError) as e:
        logger.error(f"获取{trans_base}失败，原因：{e}")
        await stats_manager.increment(source, "url", False)
        return {"code": 500, "message": str(e)}
