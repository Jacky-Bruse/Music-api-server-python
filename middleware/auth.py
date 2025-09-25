from fastapi import Request
from fastapi.responses import JSONResponse
from server.config import config
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if config.read("server.reverse_proxy"):
            request.state.remote_addr = str(
                request.headers[config.read("server.real_ip")]
            )
            request.state.host = request.base_url.hostname
            request.state.proto = str(request.headers[config.read("server.proto")])
        else:
            request.state.remote_addr = request.client.host
            request.state.host = request.base_url.hostname
            request.state.proto = request.base_url.scheme

        key_verify = config.read("security.key_verify")
        if key_verify["enable"] and request.url.path != "/":
            key = request.headers.get("X-Request-Key")
            if key not in key_verify["list"]:
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": 403,
                        "message": "KEY验证已开启",
                        "error": "X-Request-Key不在白名单中",
                    }
                )

        response = await call_next(request)
        return response
