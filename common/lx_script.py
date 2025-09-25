# ----------------------------------------
# - mode: python -
# - author: helloplhm-qwq -
# - name: lx.py -
# - project: lx-music-api-server -
# - license: MIT -
# ----------------------------------------
# This file is part of the "lx-music-api-server" project.

from . import Httpx
from . import config
from . import scheduler
from .variable import iscn
from .log import log
from aiohttp.web import Response
import ujson as json
import re

logger = log('lx_script')

jsd_mirror_list = [
    'https://cdn.jsdelivr.net',
    'https://gcore.jsdelivr.net',
    'https://fastly.jsdelivr.net',
    'https://jsd.cdn.zzko.cn',
    'https://jsdelivr.b-cdn.net',
]
githun_raw_mirror_list = [
    'https://raw.githubusercontent.com',
    'https://mirror.ghproxy.com/https://raw.githubusercontent.com',
    'https://ghraw.gkcoll.xyz',
    'https://raw.fgit.mxtrans.net',
    'https://github.moeyy.xyz/https://raw.githubusercontent.com',
    'https://raw.fgit.cf',
]

async def get_response(retry = 0):
    if (retry > 21):
        logger.warning('请求源脚本内容失败')
        return
    baseurl = '/lxmusics/lx-music-api-server/main/lx-music-source-example.js'
    jsdbaseurl = '/gh/lxmusics/lx-music-api-server@main/lx-music-source-example.js'
    try:
        i = retry
        if (i > 10):
            i = i - 11
        if (i < 5):
            req = await Httpx.AsyncRequest(jsd_mirror_list[retry] + jsdbaseurl)
        elif (i < 11):
            req = await Httpx.AsyncRequest(githun_raw_mirror_list[retry - 5] + baseurl)
        if (not req.text.startswith('/*!')):
            logger.info('疑似请求到了无效的内容，忽略')
            raise Exception from None
    except Exception as e:
        if (isinstance(e, RuntimeError)):
            if ('Session is closed' in str(e)):
                logger.error('脚本更新失败，clientSession已被关闭')
                return
        return await get_response(retry + 1)
    return req
async def get_script():
    req = await get_response()
    if (req.status == 200):
        with open('./lx-music-source-example.js', 'w') as f:
            f.write(req.text)
            f.close()
        logger.info('更新源脚本成功')
    else:
        logger.warning('请求源脚本内容失败')

async def generate_script_response(request):
    if (request.query.get('key') != config.read_config('security.key.value') and config.read_config('security.key.enable')):
        return 'key验证失败'
    try:
        with open('./lx-music-source-example.js', 'r') as f:
            script = f.read()
    except:
        return '本地无源脚本'
    scriptLines = script.split('\n')
    newScriptLines = []
    for line in scriptLines:
        line = line.strip()
        if (line.startswith('const API_URL')):
            newScriptLines.append(f'const API_URL = "{request.scheme}://{request.host}"')
        elif (line.startswith('const API_KEY')):
            newScriptLines.append(f'const API_KEY = "{config.read_config("security.key.value")}"')
        elif (line.startswith("* @name")):
            newScriptLines.append(" * @name " + config.read_config("common.download_config.name"))
        elif (line.startswith("* @description")):
            newScriptLines.append(" * @description " + config.read_config("common.download_config.intro"))
        elif (line.startswith("* @author")):
            newScriptLines.append((" * @author helloplhm-qwq & Folltoshe & " + config.read_config("common.download_config.author")) if config.read_config("common.download_config.author") else " * @author helloplhm-qwq & Folltoshe")
        elif (line.startswith("* @version")):
            newScriptLines.append(" * @version " + config.read_config("common.download_config.version"))
        elif (line.startswith("const DEV_ENABLE ")):
            newScriptLines.append("const DEV_ENABLE = " + str(config.read_config("common.download_config.dev")).lower())
        else:
            newScriptLines.append(line)
    r = '\n'.join(newScriptLines)
    
    r = re.sub(r'const MUSIC_QUALITY = {[^}]+}', f'const MUSIC_QUALITY = JSON.parse(\'{json.dumps(config.read_config("common.download_config.quality"))}\')', r)

    return Response(text = r, content_type = 'text/javascript',
                    headers = {
                        'Content-Disposition': 'attachment; filename=lx-music-source.js'
                    })

if (config.read_config('common.allow_download_script')):
    scheduler.append('update_script', get_script)
