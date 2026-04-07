# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr_app.py 
@info: Flask 应用定义 - 创建 Flask app 对象，注册 blueprints、中间件、错误处理
"""

import werkzeug.utils
import os
from datetime import timedelta
from flask import Flask, request, jsonify, make_response
from flask_socketio import SocketIO

from oddasr.logic import odd_asr_exceptions 
import oddasr.odd_asr_config as config

# from oddasr.log import logger

# register blueprints
def register_blueprints(new_app, path):
    for name in werkzeug.utils.find_modules(path):
        m = werkzeug.utils.import_string(name)
        if hasattr(m, 'bp') and m.bp is not None:
            new_app.register_blueprint(m.bp)
    new_app.errorhandler(odd_asr_exceptions.CodeException)(odd_asr_exceptions.handler)
    return new_app

app = Flask(__name__, static_url_path='')
register_blueprints(app, 'oddasr.router')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

from oddasr.router._socketio_handlers import register_handlers
register_handlers(socketio)

# 添加全局缓存控制中间件
@app.after_request
def add_cache_control(response):
    # 禁止浏览器缓存所有响应
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response
