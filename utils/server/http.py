import random
import zlib

import aiohttp

from server import variable
from utils.encode import json
from utils.server.log import createLogger
from utils.server.text import *

ua_list = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.39",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1788.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1788.0  uacq",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5666.197 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 uacq",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
]

logger = createLogger("HTTP")


def _prepare_options(options: dict) -> tuple[str, dict]:
    method = options.pop("method", "GET").upper()

    headers = options.setdefault("headers", {})
    if "User-Agent" not in headers:
        headers["User-Agent"] = random.choice(ua_list)

    if method in ("POST", "PUT"):
        if "body" in options:
            options["data"] = options.pop("body")
        if "xml" in options:
            options["data"] = options.pop("xml")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if "form" in options:
            options["data"] = convert_dict_to_form(options.pop("form"))
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if isinstance(options.get("data"), dict):
            options["data"] = json.dumps(options["data"])

    return method, options


class Response:
    def __init__(self, status: int, content: bytes, headers: dict):
        self.status_code = status
        self.content = content
        self.headers = headers
        self.text = content.decode("utf-8", errors="ignore")

    def json(self):
        try:
            if self.content.startswith((b"\x78\x9c", b"\x78\x01")):
                decompressed = zlib.decompress(self.content)
                return json.loads(decompressed)
            elif len(self.content) > 5 and self.content[5:].startswith(
                    (b"\x78\x9c", b"\x78\x01")
            ):
                decompressed = zlib.decompress(self.content[5:])
                return json.loads(decompressed)
            return json.loads(self.content)
        except:
            return {}


async def convert_to_requests_response(
        resp: aiohttp.ClientResponse,
) -> Response:
    content = await resp.content.read()
    headers = dict(resp.headers.items())

    return Response(resp.status, content, headers)


async def send_http_request(url: str, options=None) -> Response:
    if options is None:
        options = {}

    if not variable.http_client:
        variable.http_client = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                ssl=False,
            ),
            timeout=aiohttp.ClientTimeout(10.0, connect=5.0),
        )

    method, options = _prepare_options(options)

    logger.debug(f"请求开始, Method: {method}, URL: {url}, Options: {options}")

    try:
        reqattr = getattr(variable.http_client, method.lower())
    except AttributeError:
        raise AttributeError(f"不支持的类型: {method}")

    try:
        resp: aiohttp.ClientResponse = await reqattr(url, **options)
        resp.raise_for_status()

        req = await convert_to_requests_response(resp)

        logger.debug(f"请求结束，返回: {req.status_code}, {req.json()}")
        return req
    except aiohttp.ConnectionTimeoutError as e:
        logger.error(f"URL: {url} 请求超时: {str(e)}")
        raise e
    except aiohttp.ClientConnectionError as e:
        logger.error(f"URL: {url} 请求失败: {str(e)}")
        raise e
