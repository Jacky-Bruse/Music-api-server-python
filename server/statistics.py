import asyncio
import time
from pathlib import Path
from typing import Dict, Literal

from utils.encode import json
from utils.server import log

logger = log.createLogger("统计管理器")

PlatformType = Literal["kw", "kg", "tx", "wy"]
FuncType = Literal["url", "info", "lyric", "search"]


class StatisticsManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.filename = Path("data/statistics.json")
        self.data = self._load_data()
        self.total_requests = 0
        self.start_time = int(time.time())
        self._running = False
        self._task = None
        self._save_lock = asyncio.Lock()

    def _load_data(self) -> Dict:
        if self.filename.exists():
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载统计数据失败: {e}")
        else:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump({
                    platform: {
                        func: {"success": 0, "error": 0}
                        for func in ["url", "info", "lyric", "search"]
                    }
                    for platform in ["kw", "kg", "tx", "wy"]
                }, f, indent_2=True)
                print("已生成统计数据")
        return {
            platform: {
                func: {"success": 0, "error": 0}
                for func in ["url", "info", "lyric", "search"]
            }
            for platform in ["kw", "kg", "tx", "wy"]
        }

    async def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._save_loop())
            logger.info("统计管理器已启动")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._save_data()
        logger.info("统计管理器已停止")

    async def _save_loop(self):
        try:
            while self._running:
                await asyncio.sleep(10)
                await self._save_data()
        except asyncio.CancelledError:
            logger.info("统计保存任务已取消")

    async def _save_data(self):
        async with self._save_lock:
            try:
                with open(self.filename, "w", encoding="utf-8") as f:
                    json.dump(self.data, f)
            except Exception as e:
                logger.error(f"统计保存失败: {e}")

    async def increment(self, platform: PlatformType, func_type: FuncType, success: bool):
        async with self._save_lock:
            try:
                key = "success" if success else "error"
                self.data[platform][func_type][key] += 1
            except KeyError:
                logger.warning(f"无效统计项: {platform}.{func_type}")

    async def increment_request(self):
        async with self._save_lock:
            self.total_requests += 1

    def get_stats(self) -> Dict:
        return {
            "total_requests": self.total_requests,
            "platform_stats": self.data,
            "uptime": int(time.time() - self.start_time),
            "start_time": self.start_time,
        }

    def get_platform_errors(self) -> Dict[str, int]:
        errors = {}
        for platform, funcs in self.data.items():
            total_errors = sum(func_data["error"] for func_data in funcs.values())
            errors[platform] = total_errors
        return errors


stats_manager = StatisticsManager()
