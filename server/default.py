from server.models import config

default_model = config.ConfigModel(
    server=config.Server(
        host="127.0.0.1",
        port=8080,
        debug=False,
        output_logs=False,
    ),
    reverse_proxy=config.ReverseProxy(
        enable=True,
        real_ip_header="X-Real-IP",
        real_host_header="X-Real-Host",
        proto_header="X-Forwarded-Proto"
    ),
    redis=config.Redis(
        host="127.0.0.1",
        port="6379",
        db="0",
        user="default",
        password="default",
        key_prefix="default"
    ),
    script=config.Script(
        name="Name",
        author="Author",
        description="Description",
        support_qualitys={
            "kw": ["128k", "320k", "flac", "flac24bit", "hires"],
            "kg": ["128k", "320k", "flac", "flac24bit", "hires", "atmos", "master"],
            "tx": [
                "128k",
                "320k",
                "flac",
                "flac24bit",
                "hires",
                "atmos",
                "atmos_plus",
                "master",
            ],
            "wy": ["128k", "320k", "flac", "flac24bit", "hires", "atmos", "master"],
        },
        version="v1.0",
        dev=False,
        update=False,
        updateMsg="example: ver + \n + xx update"
    ),
    security=config.Security(
        userAgentBlacklist=config.UserAgentBlacklist(
            enable=True,
            list=[""]
        )
    ),
    modules=config.Modules(
        platform=config.Platform(
            kw=config.Kw(source_list=[""]),
            kg=config.Kg(mid=["musicapi"],
                         users=[config.KgUser(userid="", token="", refreshLogin=False)]),
            tx=config.Tx(users=[
                config.TxUser(uin="", token="", refreshKey="", openId="", accessToken="", refreshToken="", vipType="",
                              refreshLogin=False)], cdn_list=["http://ws.stream.music.qq.com/"]),
            wy=config.Wy(users=[""]),
        )
    )
)

default = default_model.model_dump()
