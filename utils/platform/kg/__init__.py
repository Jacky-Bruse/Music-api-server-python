from utils.encode import json
from utils.server import http
from utils.encode.dict import sort_dict
from utils.encode.md5 import create

tools = {
    "mid": "musicapi",
    "qualityHashMap": {
        "128k": "hash_128",
        "320k": "hash_320",
        "flac": "hash_flac",
        "hires": "hash_high",
        "atmos": "hash_128",
        "master": "hash_128",
    },
    "qualityMap": {
        "128k": "128",
        "320k": "320",
        "flac": "flac",
        "hires": "high",
        "atmos": "viper_atmos",
        "master": "viper_clear",
    },
}


def build_signature_params(dictionary, body=""):
    joined_str = "".join([f"{k}={v}" for k, v in dictionary.items()])
    return joined_str + body


def build_request_params(dictionary: dict):
    joined_str = "&".join([f"{k}={v}" for k, v in dictionary.items()])
    return joined_str


def sign(params, body=""):
    if isinstance(body, dict):
        body = json.dumps(body)

    params = sort_dict(params)
    params = build_signature_params(params, body)

    return create(
        "OIlwieks28dk2k092lksi2UIkp" + params + "OIlwieks28dk2k092lksi2UIkp"
    )


async def sign_request(url: str, params: dict, options: dict):
    params["signature"] = sign(
        params,
        (
            options.get("body")
            if options.get("body")
            else (
                options.get("data")
                if options.get("data")
                else (options.get("json") if options.get("json") else "")
            )
        ),
    )
    url = url + "?" + build_request_params(params)
    return await http.send_http_request(url, options)


def getKey(hash_: str, user_info: dict[str, str]) -> str:
    return create(
        hash_.lower()
        + "57ae12eb6890223e355ccfcb74edf70d"
        + "1005"
        + tools["mid"]
        + user_info["userid"]
    )