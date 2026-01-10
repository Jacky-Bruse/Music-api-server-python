import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from utils.server.ip import getIPInfo
from utils.server.log import createLogger

logger = createLogger("RequestLogger")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        try:
            ip_info = await getIPInfo(request.state.ip)
        except:
            ip_info = {"local": "Unknown"}

        logger.info(
            f"收到请求: {request.method} - {request.state.ip} - "
            f"{ip_info['local']} - {request.url.path} - "
            f"{request.query_params} - "
            f"{request.state.ua}"
        )

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response
