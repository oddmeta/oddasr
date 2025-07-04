# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_wss_server.py 
@info: 消息模版
"""

import logging
from logging import handlers
import platform

if platform.system() != "Windows":
    path = "/var/log/odd_asr.log"
else:
    path = "./odd_asr.log"

def _logging():
    FORMAT = "%(asctime)s %(levelname)s %(filename)s:%(lineno)s (%(process)s-%(thread)s) - %(message)s "
    DATE = '%Y-%m-%d %H:%M:%S'

    format = logging.Formatter(FORMAT, DATE)

    log = logging.getLogger(path)

    th = handlers.TimedRotatingFileHandler(filename=path, when='MIDNIGHT', backupCount=10, encoding='utf-8')
    th.setFormatter(format)
    log.addHandler(th)

    # stdout = logging.StreamHandler()
    # stdout.setFormatter(format)
    # log.addHandler(stdout)

    # if app.debug:
    #     enableProtoPrint = False
    #     if enableProtoPrint:
    #         logging.basicConfig(level=logging.DEBUG,
    #                             format=FORMAT,
    #                             datefmt=DATE)
    #     else:
    #         ch = logging.StreamHandler()
    #         ch.setFormatter(format)
    #         log.addHandler(ch)

    log.setLevel(logging.DEBUG)
    return log


logger = _logging()



