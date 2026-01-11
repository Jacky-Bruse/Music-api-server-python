import os

import aiohttp

running: bool = True
log_files: list = []
work_dir = os.getcwd()
http_client: aiohttp.ClientSession | None = None
