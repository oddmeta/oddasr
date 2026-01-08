# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: main_server.py 
@info: 消息模版
"""
import argparse
import threading
import asyncio
import signal
import sys
from time import sleep
from werkzeug.serving import run_simple

from oddasr.odd_asr_app import app
from oddasr.logic.odd_asr_instance import init_instance_file, init_instance_sentence
from oddasr.logic.odd_wss_server import init_instances_stream, start_wss_server
from oddasr.logic.scheduled_task import ScheduledTask
from oddasr.log import logger
from oddasr import odd_asr_config as config

# 全局变量用于控制程序退出
shutdown_flag = threading.Event()

def signal_handler(sig, frame):
    """信号处理函数，用于优雅地停止程序"""
    logger.info("接收到退出信号，正在停止所有服务...")
    shutdown_flag.set()
    
    # 停止Flask服务器（通过设置shutdown_flag，run_simple会自动停止）
    
    # 等待所有线程完成
    if 'scheduled_task' in globals():
        scheduled_task.thread_run = False
        scheduled_task.join(timeout=5)
    
    logger.info("所有服务已停止，程序退出")
    sys.exit(0)

def main():
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    def start_wss_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # 创建一个任务来运行WebSocket服务器
            server_task = loop.create_task(start_wss_server())
            
            # 等待shutdown_flag被设置
            while not shutdown_flag.is_set():
                loop.run_until_complete(asyncio.sleep(0.5))
            
            # 取消WebSocket服务器任务
            server_task.cancel()
            try:
                loop.run_until_complete(server_task)
            except asyncio.CancelledError:
                logger.info("WebSocket server task cancelled")
        finally:
            loop.close()

    # 初始化WebSocket实例
    if not config.odd_asr_cfg["disable_stream"]:
        init_instances_stream()
    
    # start websocket server
    if not config.odd_asr_cfg["disable_stream"]:
        wss_thread = threading.Thread(target=start_wss_in_thread)
        wss_thread.daemon = True  # 设置为守护线程，主线程退出时自动退出
        wss_thread.start()
        logger.info("WebSocket server started.")
    else:
        logger.info("WebSocket server disabled.")

    # init file/sentence ASR instances
    init_instance_file()
    init_instance_sentence()
    logger.info("File ASR and sentence ASR instances started.")

    # Start scheduled task thread
    global scheduled_task
    scheduled_task = ScheduledTask(status_notifier=None)
    scheduled_task.start()
    logger.info("Scheduled task thread started.")

    # Start Flask server with HTTPS support
    logger.info(f"Starting server on {'https' if config.odd_asr_cfg['enable_https'] else 'http'}://{config.HOST}:{config.PORT}")
    
    # 使用Werkzeug的run_simple替代app.run()，这样可以更好地控制服务器
    ssl_context = None
    if config.odd_asr_cfg["enable_https"]:
        ssl_context = (config.odd_asr_cfg["ssl_cert_path"], config.odd_asr_cfg["ssl_key_path"])
    
    # 运行Flask服务器，直到shutdown_flag被设置
    run_simple(
        hostname=config.HOST,
        port=config.PORT,
        application=app,
        use_reloader=False,  # 禁用自动重载
        use_debugger=config.Debug,
        ssl_context=ssl_context
    )
