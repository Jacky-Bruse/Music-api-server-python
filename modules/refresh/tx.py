from server.config import config
from utils.platform.tx import build_comm
from utils.platform.tx import sign_request
from utils.server import log

logger = log.createLogger("Refresh Login")


async def check_vip(user_info):
    options = {"req": {
        "module": "VipLogin.VipLoginInter",
        "method": "vip_login_base",
        "param": {},
    }, "comm": await build_comm(user_info)}

    req = await sign_request(options)
    body = req.json()

    if body["req"]["code"] != 0:
        logger.warning(
            f"为QQ音乐官方账号({user_info['uin']})检查VIP状态失败, code: "
            + str(body["req"]["code"])
            + f"\n响应体: {body}"
        )
        vipType = "normal"
    else:
        data = body["req"]["data"]["identity"]
        if bool(data["HugeVip"]):
            vipType = "svip"
            logger.info(
                f"QQ音乐官方账号({user_info['uin']})当前是SVIP，过期时间：{data['HugeVipEnd']}"
            )
        elif bool(data["LMFlag"]):
            vipType = "vip"
            logger.info(
                f"QQ音乐官方账号({user_info['uin']})当前是绿钻VIP，过期时间：{data['LMEnd']}"
            )
        else:
            vipType = "normal"
            logger.warning(f"QQ音乐官方账号({user_info['uin']})不是VIP")

    return vipType


async def refresh_login(user_info):
    if user_info["uin"] in [0, "", "0"]:
        return
    if user_info["token"] == "":
        return

    comm = await build_comm(user_info)
    params = {
        "comm": comm,
        "req": {
            "module": "music.login.LoginServer",
            "method": "Login",
            "param": {
                "openid": user_info["openId"],
                "access_token": user_info["accessToken"],
                "refresh_token": user_info["refreshToken"],
                "expired_in": 0,
                "musicid": int(user_info["uin"]),
                "musickey": user_info["token"],
                "refresh_key": user_info["refreshKey"],
                "loginMode": 2,
            },
        },
    }

    req = await sign_request(params)
    body = req.json()

    if body["req"]["code"] != 0:
        logger.warning(
            f"为QQ音乐官方账号({user_info['uin']})刷新登录失败, code: "
            + str(body["req"]["code"])
            + f"\n响应体: {body}"
        )
        return
    else:
        logger.info(f"为QQ音乐官方账号({user_info['uin']})刷新登录成功")

        user_list = config.get("modules.platform.tx.users")

        user_index = None
        for i, user in enumerate(user_list):
            if str(user.get("uin")) == str(user_info["uin"]):
                user_index = i
                break

        user_list[user_index]["token"] = body["req"]["data"]["musickey"]
        user_list[user_index]["uin"] = str(body["req"]["data"]["musicid"])
        user_list[user_index]["openId"] = str(body["req"]["data"]["openid"])
        user_list[user_index]["accessToken"] = str(body["req"]["data"]["access_token"])
        user_list[user_index]["refreshKey"] = str(body["req"]["data"]["refresh_key"])
        user_list[user_index]["vipType"] = await check_vip(
            {
                "uin": user_list[user_index]["uin"],
                "openId": user_list[user_index]["openId"],
                "accessToken": user_list[user_index]["accessToken"],
                "token": user_list[user_index]["token"],
                "refreshKey": user_list[user_index]["refreshKey"],
            }
        )

        config.set("modules.platform.tx.users", user_list)
        logger.info(f"为QQ音乐官方账号({user_info['uin']})数据更新完毕")
