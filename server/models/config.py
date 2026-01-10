from __future__ import annotations
from typing import List
from pydantic import BaseModel


class Server(BaseModel):
    host: str
    port: int
    debug: bool
    output_logs: bool


class ReverseProxy(BaseModel):
    enable: bool
    real_ip_header: str
    real_host_header: str
    proto_header: str


class Redis(BaseModel):
    host: str
    port: str
    db: str
    user: str
    password: str
    key_prefix: str


class Script(BaseModel):
    name: str
    author: str
    description: str
    version: str
    support_qualitys: dict[str, list[str]]
    dev: bool
    update: bool
    updateMsg: str


class UserAgentBlacklist(BaseModel):
    enable: bool
    list: List[str]


class Security(BaseModel):
    userAgentBlacklist: UserAgentBlacklist


class Kw(BaseModel):
    source_list: List[str]


class KgUser(BaseModel):
    userid: str
    token: str
    refreshLogin: bool


class Kg(BaseModel):
    mid: List[str]
    users: List[KgUser]


class TxUser(BaseModel):
    uin: str
    token: str
    refreshKey: str
    openId: str
    accessToken: str
    refreshToken: str
    vipType: str
    refreshLogin: bool


class Tx(BaseModel):
    users: List[TxUser]
    cdn_list: List[str]


class Wy(BaseModel):
    users: List[str]


class Platform(BaseModel):
    kw: Kw
    kg: Kg
    tx: Tx
    wy: Wy


class Modules(BaseModel):
    platform: Platform


class ConfigModel(BaseModel):
    server: Server
    reverse_proxy: ReverseProxy
    redis: Redis
    script: Script
    security: Security
    modules: Modules
