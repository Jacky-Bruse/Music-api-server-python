from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from server.config import config
from server.statistics import stats_manager
from utils.server.response import handleResponse


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        await stats_manager.increment_request()
        if config.get("reverse_proxy.enable"):
            request.state.ip = str(
                request.headers.get(config.get("reverse_proxy.real_ip_header"), request.client.host)
            )
            request.state.ua = request.headers.get("User-Agent", "")
            request.state.host = str(
                request.headers.get(
                    config.get("reverse_proxy.real_host_header"), request.base_url.hostname
                )
            )
            request.state.proto = str(
                request.headers.get(
                    config.get("reverse_proxy.proto_header"), request.base_url.scheme
                )
            )
        else:
            request.state.ip = request.client.host
            request.state.ua = request.headers.get("User-Agent", "")
            request.state.host = request.base_url.hostname
            request.state.proto = request.base_url.scheme

        UAblacklist = config.get("security.userAgentBlacklist")
        if UAblacklist["enable"]:
            if (not request.state.ua) or (request.state.ua in UAblacklist["list"]):
                return handleResponse(
                    {"code": 403, "message": "User-Agent异常"}
                )

        response = await call_next(request)
        return response
