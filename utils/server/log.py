import os
import sys
from typing import Any

from loguru import logger

from utils.encode import json


def get(key: str) -> Any:
    try:
        config = json.loads(open("./data/config.json", "r", encoding="utf-8").read())
        keys = key.split(".")
        value = config
        for k in keys:
            if isinstance(value, dict):
                if k not in value and keys.index(k) != len(keys) - 1:
                    value[k] = {}
                elif k not in value and keys.index(k) == len(keys) - 1:
                    value = None
                value = value[k]
            else:
                value = None
                break

        return value
    except:
        return None


_dm: bool = get("server.debug") or False
_lm: bool = get("server.output_logs") or False
debug: bool = (
    True if (os.getenv("CURRENT_ENV") == "development") else (_dm if (_dm) else False)
)
output_logs: bool = _lm if (isinstance(_lm, bool)) else True


def createLogger(name: str):
    if not hasattr(createLogger, "_initialized"):
        logger.remove()
        createLogger._initialized = True

        level = "DEBUG" if debug else "INFO"

        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <level>{message}</level>",
            level=level,
            colorize=True,
        )

    if output_logs:
        os.makedirs("./logs", exist_ok=True)
        logfile = f"./logs/{name}.log"
        level = "DEBUG" if debug else "INFO"

        logger.add(
            logfile,
            format="[{time:YYYY-MM-DD HH:mm:SS}] | [{extra[logger_name]}:{level}] | [{module}.{function}:{line}] - {message}",
            level=level,
            encoding="utf-8",
            rotation="10 MB",  # 日志文件达到 10MB 时自动轮转
            retention="30 days",  # 保留 30 天的日志
            compression="zip",  # 压缩旧日志文件
            filter=lambda record: record["extra"].get("logger_name")
                                  == name,  # 只记录当前 logger 的日志
        )

    return logger.bind(logger_name=name)


def intercept_print():
    """
    拦截 print 函数，将其重定向到 logger
    调用此函数后，所有 print() 输出都会被记录到日志中
    """
    import builtins

    original_print = builtins.print

    def custom_print(*args, **kwargs):
        # 提取 print 函数的参数
        sep = kwargs.get("sep", " ")
        kwargs.get("end", "\n")
        file = kwargs.get("file", None)

        # 如果指定了 file 参数，使用原始 print
        if file is not None:
            original_print(*args, **kwargs)
            return

        # 将参数转换为字符串
        message = sep.join(str(arg) for arg in args)

        # 使用 logger 输出（去除末尾的换行符）
        logger.info(f"[PRINT] {message}")

    builtins.print = custom_print

    logger.success("Print 函数已被拦截，所有 print 输出将记录到日志")
