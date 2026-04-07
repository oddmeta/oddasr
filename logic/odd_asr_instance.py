# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr_instance.py 
@info: ASR实例管理
"""

from oddasr.log import logger

from oddasr.logic.odd_asr_file import OddAsrFile, OddAsrParamsFile
from oddasr.logic.odd_asr_sentence import OddAsrSentence, OddAsrParamsSentence
import oddasr.odd_asr_config as config

# File ASR
odd_asr_params_file = OddAsrParamsFile()
odd_asr_file_set = set()

def init_instance_file():
    global odd_asr_file_set
    for i in range(config.odd_asr_cfg["asr_file_cfg"]["max_instance"]):
        odd_asr_file = OddAsrFile(odd_asr_params_file)
        odd_asr_file_set.add(odd_asr_file)

def find_free_odd_asr_file():
    '''
    find a free odd_asr_file
    :param :
    :return:
    '''
    global odd_asr_file_set
    for odd_asr_file in odd_asr_file_set:
        if not odd_asr_file.is_busy():
            return odd_asr_file
        
    return None

# Sentence ASR
odd_asr_params_sentence = OddAsrParamsSentence()
odd_asr_sentence_set = set()

def init_instance_sentence():
    global odd_asr_sentence_set
    for i in range(config.odd_asr_cfg["asr_sentence_cfg"]["max_instance"]):
        odd_asr_sentence = OddAsrSentence(odd_asr_params_sentence)
        odd_asr_sentence_set.add(odd_asr_sentence)

def find_free_odd_asr_sentence():
    '''
    find a free odd_asr_sentence
    :param :
    :return:
    '''
    global odd_asr_sentence_set
    for odd_asr_sentence in odd_asr_sentence_set:
        if not odd_asr_sentence.is_busy():
            return odd_asr_sentence
        
    return None
