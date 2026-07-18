# -*- coding: utf-8 -*-
"""
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm
@file: odd_asr_instance.py
@info: ASR实例管理
"""

import threading
from collections import deque

from log import logger

from odd_asr_file import OddAsrFile, OddAsrParamsFile
from odd_asr_sentence import OddAsrSentence, OddAsrParamsSentence
import odd_asr_config as config

class InstancePool:
    """线程安全的实例池，O(1) 获取和释放"""

    def __init__(self):
        self._idle = deque()
        self._busy = set()
        self._lock = threading.Lock()

    def add(self, instance):
        with self._lock:
            self._idle.append(instance)

    def acquire(self):
        """获取一个空闲实例，返回实例或 None"""
        with self._lock:
            if not self._idle:
                return None
            instance = self._idle.popleft()
            self._busy.add(instance)
            return instance

    def release(self, instance):
        """释放实例回空闲池"""
        with self._lock:
            self._busy.discard(instance)
            self._idle.append(instance)

    def find_by_session_id(self, session_id_getter, task_id):
        """按 session_id 查找实例（遍历忙碌集合）"""
        with self._lock:
            for inst in self._busy:
                if session_id_getter(inst) == task_id:
                    return inst
        return None

    def find_by_websocket(self, websocket_getter, websocket):
        """按 websocket 查找实例"""
        with self._lock:
            for inst in self._busy:
                if websocket_getter(inst) == websocket:
                    return inst
        return None

    @property
    def idle_count(self):
        return len(self._idle)

    @property
    def busy_count(self):
        return len(self._busy)


# File ASR
odd_asr_params_file = OddAsrParamsFile()
odd_asr_file_pool = InstancePool()

def init_instance_file():
    for i in range(config.odd_asr_cfg["asr_file_cfg"]["max_instance"]):
        odd_asr_file_pool.add(OddAsrFile(odd_asr_params_file))

def find_free_odd_asr_file():
    return odd_asr_file_pool.acquire()

def release_odd_asr_file(instance):
    odd_asr_file_pool.release(instance)

# Sentence ASR
odd_asr_params_sentence = OddAsrParamsSentence()
odd_asr_sentence_pool = InstancePool()

def init_instance_sentence():
    for i in range(config.odd_asr_cfg["asr_sentence_cfg"]["max_instance"]):
        odd_asr_sentence_pool.add(OddAsrSentence(odd_asr_params_sentence))

def find_free_odd_asr_sentence():
    return odd_asr_sentence_pool.acquire()

def release_odd_asr_sentence(instance):
    odd_asr_sentence_pool.release(instance)
