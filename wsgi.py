# -*- coding: utf-8 -*-
"""
WSGI 入口模块
用法: gunicorn -c gunicorn_config.py wsgi:app

模块级别初始化：WS 线程 + ASR 实例 + 定时任务
Gunicorn worker 导入此模块时自动完成所有初始化
"""

import threading
import asyncio

from log import logger
from odd_asr_app import app
import odd_asr_config as asr_config

# 初始化 ASR 实例
from odd_asr_instance import init_instance_file, init_instance_sentence
from scheduled_task import ScheduledTask

init_instance_file()
init_instance_sentence()
logger.info("ASR instances initialized (wsgi).")

# 启动定时任务
scheduled_task = ScheduledTask(status_notifier=None)
scheduled_task.start()

# 启动 WebSocket server 线程
if not asr_config.odd_asr_cfg["disable_stream"]:
    from odd_wss_server import start_wss_server

    def _start_wss():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_wss_server())
        finally:
            loop.close()

    _wss_thread = threading.Thread(target=_start_wss, daemon=True)
    _wss_thread.start()
    logger.info("WebSocket server started (wsgi).")

logger.info("wsgi.py initialization complete.")
