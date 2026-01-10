import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from middleware.auth import AuthMiddleware
from middleware.request_logger import RequestLoggerMiddleware
from modules.refresh.kg import refresh_login as kg_refreshLogin
from modules.refresh.tx import refresh_login as tx_refreshLogin
from routers import (
    home,
    script,
    music
)
from server import variable
from server.config import config
from utils.server.log import createLogger, intercept_print

logger = createLogger("Main")
scheduler = AsyncIOScheduler(job_defaults={"misfire_grace_time": 3600})


def reg_refresh_login_pool_task():
    tx_user_info_pool = config.get("modules.platform.tx.users")
    for tx_user_info in tx_user_info_pool:
        if tx_user_info["refreshLogin"]:
            scheduler.add_job(
                tx_refreshLogin,
                "interval",
                seconds=86400,
                kwargs={"user_info": tx_user_info},
                id=f"刷新ck_QQ音乐: {tx_user_info['uin']}",
                next_run_time=datetime.now(),
            )
            logger.info(f"已注册定时任务: 刷新ck_QQ音乐: {tx_user_info['uin']}")

    kg_user_info_pool = config.get("modules.platform.kg.users")
    for user_info in kg_user_info_pool:
        if user_info["refreshLogin"]:
            scheduler.add_job(
                kg_refreshLogin,
                "interval",
                seconds=86400,
                kwargs={"user_info": user_info},
                id=f"刷新ck_酷狗音乐: {user_info['userid']}",
                next_run_time=datetime.now(),
            )
            logger.info(f"已注册定时任务: 刷新ck_酷狗音乐: {user_info['userid']}")

    logger.info(f"当前已注册任务: {scheduler.get_jobs()}")


@asynccontextmanager
async def lifespan(app):
    intercept_print()
    reg_refresh_login_pool_task()
    scheduler.start()

    yield

    scheduler.shutdown()

    if variable.http_client:
        await variable.http_client.connector.close()
        await variable.http_client.close()
        logger.info("Aiohttp Session closed")

    for f in variable.log_files:
        if f and hasattr(f, "close"):
            f.close()

    pid = os.getpid()
    logger.info(f"[{pid}] Server closed")


app = FastAPI(
    title="lx-music-api-server",
    summary="Unofficial LX Music 's Backend. Uses: FastAPI, Uvicorn, Aiohttp",
    version="3.0.0",
    lifespan=lifespan,
)

# add middleware
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(AuthMiddleware)
# add route
app.include_router(home.router)
app.include_router(script.router)
app.include_router(music.router)


async def main():
    server = uvicorn.Server(uvicorn.Config(
        app,
        host=config.get("server.host"),
        port=config.get("server.port"),
    ))
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass