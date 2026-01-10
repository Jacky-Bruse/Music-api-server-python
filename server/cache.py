import sys

import redis

from server.config import config
from server.exceptions import CacheReadException, CacheWriteException, CacheDeleteException
from utils.encode import json
from utils.server import log


def build_key(module: str, key: str):
    prefix = config.get("redis.key_prefix")
    return f"{prefix}:{module}:{key}"


class CacheManager:
    def __init__(self):
        self.logger = log.createLogger("Cache")
        self.redis = self.connect()
        self.logger.info("已初始化缓存管理器")

    def connect(self):
        try:
            host = config.get("redis.host")
            port = config.get("redis.port")
            user = config.get("redis.user")
            password = config.get("redis.password")
            db = config.get("redis.db")
            client = redis.Redis(
                host=host, port=port, username=user, password=password, db=db
            )
            if not client.ping():
                raise Exception("Ping 数据库失败")
            return client
        except Exception as e:
            self.logger.error(f"连接Redis缓存数据库失败: {e}")
            sys.exit(1)

    def get(self, module: str, key: str):
        try:
            key = build_key(module, key)
            result = self.redis.get(key)
            if result:
                cache_data = json.loads(result)
                return cache_data
        except BaseException as e:
            self.logger.error("缓存读取遇到错误…")
            raise CacheReadException(e)

    def set(self, module: str, key: str, data: str | dict | list, expire: int = None):
        try:
            key = build_key(module, key)
            self.redis.set(
                key, json.dumps(data), ex=expire if expire and expire > 0 else None
            )
        except BaseException as e:
            self.logger.error("缓存写入遇到错误…")
            raise CacheWriteException(e)

    def delete(self, module: str, key: str):
        try:
            key = build_key(module, key)
            self.redis.delete(key)
        except BaseException as e:
            self.logger.error("缓存删除遇到错误…")
            raise CacheDeleteException(e)

cache = CacheManager()
