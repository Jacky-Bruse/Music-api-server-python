import time
from importlib import import_module
from typing import Dict

from server.cache import cache
from server.exceptions import FailedException
from server.models.music import SongInfo
from server.statistics import stats_manager
from utils.server import log
from . import kg
from . import kw
from . import tx
from . import wy

logger = log.createLogger("INFO Module")
INFO_CACHE_EXPIRE = 86400 * 3


def require(module: str):
    try:
        parts = module.split(".")
        mod = import_module(parts[0])
        for part in parts[1:]:
            mod = getattr(mod, part)
        return mod
    except (ImportError, ValueError, AttributeError):
        raise ImportError("未知的源/不支持的方法", name=module)


async def getSongInfo(source: str, songId: str | int) -> Dict:
    try:
        cache_key = f"{source}_{songId}"
        cache_result = cache.get("info", cache_key)

        if cache_result:
            logger.info(f"使用缓存的info_{cache_key}")
            await stats_manager.increment(source, "info", True)
            return {"code": 200, "message": "成功", "data": cache_result["data"]}

        func = require(f"modules.info.{source}.getMusicInfo")
        result: SongInfo = (
            await func(songId) if source != "kg" else (await func(songId))[0]
        )

        logger.info(
            f"获取info_{source}_{result.songName}_{result.artistName}_{result.albumName}成功"
        )

        expireAt = int(time.time() + INFO_CACHE_EXPIRE)
        cache.set(
            "info",
            cache_key,
            {
                "data": result.model_dump(),
                "time": expireAt,
                "expire": True,
            },
            INFO_CACHE_EXPIRE,
        )
        logger.debug(f"缓存已更新: info_{cache_key}")

        await stats_manager.increment(source, "info", True)
        return {"code": 200, "message": "成功", "data": result.model_dump()}

    except(FailedException, ImportError) as e:
        logger.error(f"获取info_{source}_{songId}失败：{e}")
        await stats_manager.increment(source, "info", False)
        return {"code": 500, "message": str(e)}
