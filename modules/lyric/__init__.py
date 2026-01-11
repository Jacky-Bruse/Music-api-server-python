import time
from importlib import import_module
from typing import Dict

from modules import info
from server.cache import cache
from server.exceptions import FailedException
from server.statistics import stats_manager
from utils.server import log
from . import kg
from . import kw
from . import tx
from . import wy

logger = log.createLogger("LYRIC Module")
LYRIC_CACHE_EXPIRE = 86400 * 3


def require(module: str):
    try:
        parts = module.split(".")
        mod = import_module(parts[0])
        for part in parts[1:]:
            mod = getattr(mod, part)
        return mod
    except (ImportError, ValueError, AttributeError):
        raise ImportError("未知的源/不支持的方法", name=module)


async def getLyric(source: str, songId: str | int) -> Dict:
    try:
        cache_key = f"{source}_{songId}"
        cache_result = cache.get("lyric", cache_key)

        if cache_result:
            logger.info(f"使用缓存的lyric_{cache_key}")
            await stats_manager.increment(source, "lyric", True)
            return {"code": 200, "message": "成功", "data": cache_result["data"]}

        if source == "tx":
            songinfo = await info.tx.getMusicInfo(songId)
            songId = songinfo.songId
            cache_key = f"{source}_{songId}"

        func = require(f"modules.lyric.{source}.getLyric")
        result = await func(songId)
        result = result.model_dump()
        expireAt = int(time.time() + LYRIC_CACHE_EXPIRE)
        cache.set(
            "lyric",
            cache_key,
            {
                "data": result,
                "time": expireAt,
                "expire": True,
            },
            LYRIC_CACHE_EXPIRE,
        )
        logger.debug(f"缓存已更新: lyric_{cache_key}")

        await stats_manager.increment(source, "lyric", True)
        return {"code": 200, "message": "成功", "data": result}

    except (FailedException, ImportError) as e:
        logger.error(f"获取lyric_{source}_{songId}失败：{e}")
        await stats_manager.increment(source, "lyric", False)
        return {"code": 500, "message": str(e)}
