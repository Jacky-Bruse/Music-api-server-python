import re

from fastapi import APIRouter, Request, Response

from server.config import config
from utils.encode import json
from utils.encode.md5 import create
from utils.server.response import handleResponse

router = APIRouter()


def build_url(request: Request) -> str:
    scheme = request.scope.get("scheme", "http")
    server = request.scope.get("server")

    if config.get("reverse_proxy.enable"):
        return f"{request.state.proto}://{request.state.host}{':' + str(request.url.port) if request.url.port else ''}"

    if server:
        host, port = server
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"

        if (scheme == "http" and port != 80) or (scheme == "https" and port != 443):
            return f"{scheme}://{host}:{port}"
        else:
            return f"{scheme}://{host}"

    host = request.state.host
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"

    return f"{request.state.proto}://{host}"


@router.get("/script")
async def lx_script(request: Request, key: str | None = None):
    name = config.get("script.name")
    author = config.get("script.author")
    version = config.get("script.version")
    description = config.get("script.description")
    supported_qualitys = config.get("script.support_qualitys")

    with open("./static/lx-source.js", "r", encoding="utf-8") as f:
        script = f.read()

    scriptLines = script.split("\n")
    newScriptLines = []

    for line in scriptLines:
        oline = line
        line = line.strip()
        url = build_url(request)
        if line.startswith("const API_URL"):
            newScriptLines.append(f'''const API_URL = "{url}"''')
        elif line.startswith("const API_KEY"):
            newScriptLines.append(f'''const API_KEY = "{key if key else ""}"''')
        elif line.startswith("* @name"):
            newScriptLines.append(" * @name " + name)
        elif line.startswith("* @description"):
            newScriptLines.append(" * @description " + description)
        elif line.startswith("* @author"):
            newScriptLines.append(" * @author " + author)
        elif line.startswith("* @version"):
            newScriptLines.append(
                " * @version " + version
            )
        elif line.startswith("const DEV_ENABLE "):
            newScriptLines.append(
                "const DEV_ENABLE = " + str(config.get("script.dev")).lower()
            )
        elif line.startswith("const UPDATE_ENABLE "):
            newScriptLines.append(
                "const UPDATE_ENABLE = "
                + str(config.get("script.update")).lower()
            )
        else:
            newScriptLines.append(oline)

    r = "\n".join(newScriptLines)

    r = re.sub(
        r"const MUSIC_QUALITY = {[^}]+}",
        f"const MUSIC_QUALITY = JSON.parse('{json.dumps(supported_qualitys)}')",
        r,
    )

    if config.get("script.update"):
        md5 = create(r)
        r = r.replace(r'const SCRIPT_MD5 = "";', f'const SCRIPT_MD5 = "{md5}";')
        if request.query_params.get("checkUpdate"):
            if request.query_params.get("checkUpdate") == md5:
                return handleResponse({"code": 200, "message": "成功"})
            url = build_url(request)
            updateUrl = f"{url}/script{('?key=' + key) if key else ''}"
            updateMsg = (
                str(config.get("script.updateMsg"))
                .format(
                    updateUrl=updateUrl,
                    url=url,
                    key=key,
                    version=version,
                )
                .replace("\\n", "\n")
            )
            return handleResponse(
                {
                    "code": 200,
                    "message": "成功",
                    "data": {"updateMsg": updateMsg, "updateUrl": updateUrl},
                },
            )

    return Response(
        content=r,
        media_type="text/javascript",
        headers={
            "Content-Disposition": """attachment; filename=ikun-music-source.js"""
        },
    )

