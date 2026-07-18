# -*- coding: utf-8 -*-
"""
Gunicorn 生产级 WSGI 配置
用法: gunicorn -c gunicorn_config.py wsgi:app
"""

import odd_asr_config as asr_config
from log import logger


# ============================================================
# Server socket
# ============================================================

bind = f"{asr_config.HOST}:{asr_config.PORT}"
backlog = 2048

# ============================================================
# Worker processes
# ============================================================

workers = 1
threads = 4
worker_class = "gthread"
timeout = 120
keepalive = 5
preload_app = False


def on_starting(server):
    logger.info(f"Gunicorn starting: bind={bind}, workers={workers}, "
                f"threads={threads}, worker_class={worker_class}")
