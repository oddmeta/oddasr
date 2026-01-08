# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr.py 
@info: 消息模版
"""

import os
import uuid
import wave

from flask import Blueprint, request, jsonify
from mutagen.mp3 import MP3

# import app
from oddasr.log import logger
from oddasr.logic.odd_asr_instance import find_free_odd_asr_file, find_free_odd_asr_sentence
from oddasr.logic.scheduled_task import ScheduledTask
from oddasr.logic.odd_asr_file import OddAsrFile
from oddasr.logic.odd_asr_sentence import OddAsrSentence

########################################
## main
########################################
bp = Blueprint('asr', __name__, url_prefix='')

@bp.route('/v1/asr/sentence', methods=['POST'])
def transcribe_sentence():
    """
    Receive an audio file from the client and return the transcribed text.
    """
    return_ok = True
    try:

        # Get the uploaded audio file
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({"error": "Invalid parameter. audio param is required."}), 400
        
        # get mode from request if provided
        mode = request.form.get('mode', "file")  # mode should be a string like 'file', 'stream', 'pipeline'
        output_format = request.form.get('output_format', "txt")  # output_format should be a string like 'txt', 'srt', 'spk'
        hotwords = request.form.get('hotwords', "")  # hotwords should be a string like 'word1 word2'

        # Create a temporary directory with proper permissions
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"temp_audio_{os.urandom(8).hex()}.wav")

        # Save the audio file to a temporary location
        try:
            audio_file.save(temp_path)
            logger.info(f"Received audio and saved to: {temp_path}")
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            return jsonify({"error": f"Failed to save audio file: {str(e)}"}), 500

        # find a odd_asr_file instance
        odd_asr_sentence: OddAsrSentence = find_free_odd_asr_sentence()
        
        if not odd_asr_sentence:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return_ok = False
            result = "no available asr instance."
            return jsonify({"error": result}), 500

        # recognition with hotwords
        try:
            if mode == "file":
                result = odd_asr_sentence.transcribe_sentence(audio_file=temp_path, hotwords=hotwords, output_format=output_format)
            else:
                return_ok = False
                result = f"unsupported mode: {mode}."
        except Exception as e:
            logger.error(f"ASR processing error: {e}")
            result = f"ASR processing error: {str(e)}"
            return_ok = False
        finally:
            # Delete the temporary file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"Deleted temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")

        logger.info(f"Recognized mode:{mode}, fmt={output_format}, result: {result[:100]}...")

        # Return the recognition result
        if not return_ok:
            return jsonify({"error": result}), 500
        else:
            return jsonify({"text": result}), 200

    except Exception as e:
        logger.error(f"Unexpected error in transcribe endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp.route('/v1/asr/file', methods=['POST'])
def transcribe():
    """
    Receive an audio file from the client and return the transcribed text.
    """
    return_ok = True
    try:

        # Get the uploaded audio file
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({"error": "Invalid parameter. audio param is required."}), 400
        
        # get mode from request if provided
        mode = request.form.get('mode', "file")  # mode should be a string like 'file', 'stream', 'pipeline'
        output_format = request.form.get('output_format', "txt")  # output_format should be a string like 'txt', 'srt', 'spk'
        hotwords = request.form.get('hotwords', "")  # hotwords should be a string like 'word1 word2'

        # Create a temporary directory with proper permissions
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"temp_audio_{os.urandom(8).hex()}.wav")

        # Save the audio file to a temporary location
        try:
            audio_file.save(temp_path)
            logger.info(f"Received audio and saved to: {temp_path}")
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            return jsonify({"error": f"Failed to save audio file: {str(e)}"}), 500


        logger.info(f"mode:{mode}, fmt={output_format}...")

        result = {

        }

        # Return the recognition result
        if not return_ok:
            return jsonify({"error": result}), 500
        else:
            return jsonify({"text": result}), 200

    except Exception as e:
        logger.error(f"Unexpected error in transcribe endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp.route('/v1/asr/file/upload', methods=['POST'])
def file_upload():
    return jsonify({"text": "OK"}), 200

@bp.route('/v1/asr/task/delete', methods=['POST'])
def asr_recorder_delete_task():
    return jsonify({"text": "OK"}), 200

@bp.route('/v1/asr/task/create', methods=['POST'])
def asr_task_create():
    """
    Receive an audio file from the client and return the transcribed text.
    
    """
    file = request.files.get('file')
    file_content = file.read()
    size = len(file_content)

    # check
    if size > 512 * 1024 * 1024:
        return {'error_code': -2, 'error_desc': 'file size > 512m', 'data': {'task_id': ""}}
    
    hot_uid = ''
    sensitive_uid = ''
    if request.form.get('hot_uid', None):
        hot_uid = str(request.form['hot_uid'])

    if request.form.get('sensitive_uid', None):
        sensitive_uid = str(request.form['sensitive_uid'])

    unique_id = hot_uid + ";" + sensitive_uid

    priority = request.form['priority']
    if not all([file]):
        return {'error_code': -1, 'error_desc': 'params is null', 'data': {'task_id': ''}}
    logger.info("create task unique_id: " + str(unique_id) + " filename: " + str(file.filename))
    file_uuid = uuid.uuid1()
    file_path = "tmp/" + str(file_uuid) + "_" + str(file.filename)
    try:
        with open(file_path, "wb+") as f:
            f.write(file_content)
            f.close()
    except:
        logger.info("file error")
        return {'error_code': -3, 'error_desc': 'server can not create the file', 'data': {'task_id': ""}}

    # 采样率
    frame_rate = 0
    # 几通道
    channel = 2

    # 判断文件格式
    try:
        song = wave.open(file_path)
        frame_rate = song.getframerate()
        channel = song.getnchannels()
        is_type_ok = True
    except:
        is_type_ok = False

    if not is_type_ok:
        try:
            song = MP3(file_path)
            frame_rate = song.info.sample_rate
            channel = song.info.channels
            is_type_ok = True
        except:
            is_type_ok = False

    if not is_type_ok:
        return {'error_code': -2, 'error_desc': '必须是mp3或者wav', 'data': {'task_id': ""}}

    # 判断采样率
    if frame_rate not in (8000, 16000):
        return {'error_code': -2, 'error_desc': '采样率必须是8000或者16000HZ', 'data': {'task_id': ""}}
    # 判断几通道
    if channel != 1:
        return {'error_code': -2, 'error_desc': '必须是单通道', 'data': {'task_id': ""}}

    task_id = ScheduledTask.start_task(priority, unique_id, file_path)
    if task_id is not None:
        ScheduledTask.is_transmit = True
        return {'error_code': 0, 'error_desc': 'ok', 'data': {'task_id': task_id}}
    return {'error_code': -2, 'error_desc': 'create task fail', 'data': {'task_id': ""}}
@bp.route('/v1/asr/task/status', methods=['POST'])
def asr_task_status():
    return jsonify({"text": "OK"}), 200
@bp.route('/v1/asr/task/cancel', methods=['POST'])
def asr_task_cancel():
    return jsonify({"text": "OK"}), 200

@bp.route('/update_transmit', methods=['POST'])
def update_transmit():
    return jsonify({"text": "OK"}), 200

@bp.route('/api/v2/asr/lm/bases', methods=['GET'])
def get_lm_bases():
    # 系统启动时会自动尝试创建基础模型，可以通过下面的命令确认是否基础模型已经创建：
    # curl -X GET \
    #  --header 'Content-Type: multipart/form-data' \
    #  --header 'Accept: application/json' \
    #  --header 'X-NLS-Token: default' \
    #  'http://nls-slp.aliyun.test:8701/api/v2/asr/lm/bases'
    # 如果返回的结果里 total_items 的值不是 0，表示系统已经存在定制模
    j = {"total_items": 0}
    return jsonify(j), 200

@bp.route('/api/v1/asr/class-vocabs', methods=['POST'])
def add_class_vocab():
    # 5.4.定制类热词
    # 执行下面的命令添加类热词，这里我们添加了“北京”和“上海”这两个地名：（参考 7.6.1 节）
    # curl -X POST \
    # --header 'Content-Type: application/json' --header 'Accept: application/json' \
    # --header 'X-NLS-User: default' --header 'X-NLS-Token: default' \
    # -d '{
    # "id": "demo-vocab",
    # "name": "示例词表",
    # "description": "这是一个示例词表",
    # "words": ["北京", "上海"]
    # }' 'http://nls-slp.aliyun.test:8701/api/v1/asr/class-vocabs'


    # 7.6.1.创建词表
    # 路径：
    # POST /api/v1/asr/class-vocabs
    # 描述：
    # 创建一个定制类热词词表。

    # 输入参数：
    # 名称 位置 说明
    # vocab Body 类热词词表对象（AsrClassVocab）。可以设置如下参数：
    # id：词表 ID，可选，如果为空则自动生成；
    # name：词表名称；
    # description：词表描述信息，可选；
    # words：要添加的词，是一个字符串数组。

    # 请求示例：
    # curl -X POST \
    #  --header 'Content-Type: application/json' --header 'Accept: application/json' \
    #  --header 'X-NLS-User: default' --header 'X-NLS-Token: default' \
    #  -d '{
    #  "id": "demo-vocab",
    #  "name": "示例词表",
    #  "description": "这是一个示例词表",
    #  "words": ["苹果", "西瓜"]
    # }' 'http://nls-slp.aliyun.test:8701/api/v1/asr/class-vocabs'

    # 输出参数：
    # 名称 说明
    # class_vocab _id 词表 ID。

    # 响应示例：
    # {
    #  "request_id": "7130914d32a3441db06747523675d9ff",
    #  "class_vocab_id": "demo-vocab"
    # }

    j = {
            "request_id": "7130914d32a3441db06747523675d9ff",
            "class_vocab_id": "demo-vocab"
        }

    return jsonify(j), 200

@bp.route('/api/v1/asr/class-vocabs', methods=['GET'])
def get_class_vocabs():
    # 7.6.2.列举词表
    # 路径：
    # GET /api/v1/asr/class-vocabs
    # 描述：
    # 列举定制类热词词表。

    # 输入参数：
    # 名称 位置 说明
    # page_number Query 页号，从 1 开始编号。可选，默认值是 1。
    # page_size Query 页大小，范围在 1 到 100 之间。可选，默认是 10。

    # 请求示例：
    # curl -X GET --header 'Accept: application/json' \
    # --header 'X-NLS-User: default' --header 'X-NLS-Token: default' \
    # 'http://nls-slp.aliyun.test:8701/api/v1/asr/class-vocabs'

    # 输出参数：
    # 名称 说明
    # page 类热词词表对象（AsrClassVocab）的分页结果。

    # 响应示例：
    # {
    # "request_id": "7130914d32a3441db06747523675d9ff",
    # "page": {
    # "content": [
    # {
    # "id": "demo-vocab",
    # "name": "示例词表",
    # "description": "这是一个示例词表",
    # "size": 4,
    # "md5": "f1d3ff8443297732862df21dc4e57262",
    # "create_time": "2018-11-01 20:02:56",
    # "update_time": "2018-11-01 20:02:56"
    # }
    # ],
    # "total_pages": 1,
    # "total_items": 1,
    # "page_number": 1,
    # "page_size": 10
    # }
    # }

    j = {
        "request_id": "7130914d32a3441db06747523675d9ff",
        "page": {
            "content": [
                {
                    "id": "demo-vocab",
                    "name": "示例词表",
                    "description": "这是一个示例词表",
                    "size": 4,
                    "md5": "f1d3ff8443297732862df21dc4e57262",
                    "create_time": "2018-11-01 20:02:56",
                    "update_time": "2018-11-01 20:02:56"
                }
            ],
            "total_pages": 1,
            "total_items": 1,
            "page_number": 1,
            "page_size": 10
        }
    }

    return jsonify(j), 200

@bp.route('/api/v1/asr/class-vocabs/<vocab_id>', methods=['GET'])
def get_class_vocab(vocab_id):
    # 7.6.3.查询词表
    # 路径：
    # GET /api/v1/asr/class-vocabs/{vocab_id}
    # 描述：
    # 查询定制类热词词表。
    # 输入参数：
    # 名称 位置 说明
    # vocab_id Path 要查询的词表 ID。
    # 请求示例：
    # curl -X GET --header 'Accept: application/json' \
    #  --header 'X-NLS-User: default' --header 'X-NLS-Token: default' \
    #  'http://nls-slp.aliyun.test:8701/api/v1/asr/class-vocabs/demo-vocab'
    # 输出参数：
    # 名称 说明
    # class_vocab 类热词词表对象（AsrClassVocab）。
    # 响应示例：
    # {
    #  "request_id": "7130914d32a3441db06747523675d9ff",
    #  "class_vocab": {
    #  "id": "demo-vocab",
    #  "name": "示例词表（二）",
    #  "description": "这是另一个示例词表",
    #  "size": 4,
    #  "md5": "f1d3ff8443297732862df21dc4e57262",
    #  "words": [
    #  "苹果",
    #  "西瓜"
    #  ],
    #  "create_time": "2018-11-01 18:31:06",
    #  "update_time": "2018-11-01 18:31:06"
    #  }
    # }

    j = {
        "request_id": "7130914d32a3441db06747523675d9ff",
        "class_vocab": {
            "id": "demo-vocab",
            "name": "示例词表（二）",
            "description": "这是另一个示例词表",
            "size": 4,
            "md5": "f1d3ff8443297732862df21dc4e57262",
            "words": [
                "苹果",
                "西瓜"
            ],
            "create_time": "2018-11-01 18:31:06",
            "update_time": "2018-11-01 18:31:06"
        }
    }

    return jsonify(j), 200


@bp.route('/api/v1/asr/class-vocabs', methods=['PUT'])
def update_class_vocab():
    # 7.6.4.更新词表
    # 路径：
    # POST /api/v1/asr/class-vocabs
    # 描述：
    # 更新定制类热词词表。
    # 输入参数：
    # 名称 位置 说明
    # vocab Body 类热词词表对象（AsrClassVocab）。可以设置如下参数：
    # id：词表 ID，可选，如果为空则自动生成；
    # name：词表名称；
    # description：词表描述信息，可选；
    # words：要添加的词，是一个字符串数组，全量替换原有的词。
    # 请求示例：
    # curl -X PUT \
    #  --header 'Content-Type: application/json' --header 'Accept: application/json' \
    #  --header 'X-NLS-User: default' --header 'X-NLS-Token: default' -d '{
    #  "id": "demo-vocab",
    #  "name": "示例词表（二）",
    #  "description": "这是另一个示例词表",
    #  "words": ["苹果", "西瓜"]
    # }' 'http://nls-slp.aliyun.test:8701/api/v1/asr/class-vocabs'
    # 输出参数：
    # 名称 说明
    # request_id 请求 ID。
    # 响应示例：
    # {
    #  "request_id": "7130914d32a3441db06747523675d9ff"
    # }

    j = {"request_id": "7130914d32a3441db06747523675d9ff"}

    return jsonify(j), 200

@bp.route('/api/v1/asr/class-vocabs/<vocab_id>', methods=['DELETE'])
def delete_class_vocab(vocab_id):
    # 7.6.5.删除词表
    # 路径：
    # DELETE /api/v1/asr/class-vocabs/{vocab_id}
    # 描述：
    # 删除定制类热词词表。
    # 输入参数：
    # 名称 位置 说明
    # vocab_id Path 要删除的词表 ID。
    # 请求示例：
    # curl -X DELETE --header 'Accept: application/json' \
    #  --header 'X-NLS-User: default' --header 'X-NLS-Token: default' \
    #  'http://nls-slp.aliyun.test:8701/api/v1/asr/class-vocabs/demo-vocab'
    # 输出参数：
    # 名称 说明
    # request_id 请求 ID。
    # 响应示例：
    # {
    #  "request_id": "7130914d32a3441db06747523675d9ff"
    # }
    j = {"request_id": "7130914d32a3441db06747523675d9ff"}

    return jsonify(j), 200

@bp.route('/api/v1/asr/vocabs', methods=['POST'])
def add_vocab(vocab_id):
    # 7.7.1.创建词表
    # 路径：
    # POST /api/v1/asr/vocabs
    # 输入参数：
    # 名称 位置 说明
    # vocab Body 泛热词词表对象（AsrVocab）。可以设置如下参数：
    # id：词表 ID，可选，如果为空则自动生成；
    # name：词表名称；
    # description：词表描述信息，可选；
    # word_weights：要添加的词，是一个词典，键为词，值为权重。
    # 请求示例：
    # curl -X POST \
    # --header 'Content-Type: application/json' \
    # --header 'Accept: application/json' \
    # --header 'X-NLS-User: default' \
    # --header 'X-NLS-Token: default' \
    # -d '{
    # "id": "demo-vocab",
    # "name": "示例词表",
    # "description": "这是一个示例词表",
    # "word_weights": {"苹果": 2, "西瓜": 3}
    # }' 'http://nls-slp.aliyun.test:8701/api/v1/asr/vocabs'
    # 输出参数：
    # 名称 说明
    # vocab _id 词表 ID。
    # 响应示例：
    # {
    # "request_id": "7130914d32a3441db06747523675d9ff",
    # "vocab_id": "demo-vocab"
    # }

    j = {"request_id": "7130914d32a3441db06747523675d9ff", "vocab_id": "demo-vocab"}

    return jsonify(j), 200

@bp.route('/api/v1/asr/vocabs', methods=['GET'])
def get_vocabs():
    # 7.7.2.列举词表
    # 路径：
    # GET /api/v1/asr/vocabs
    # 输入参数：
    # 名称 位置 说明
    # page_number Query 页号，从 1 开始编号。可选，默认值是 1。
    # page_size Query 页大小，范围在 1 到 100 之间。可选，默认是 10。
    # 请求示例：
    # curl -X GET \
    # --header 'Accept: application/json' \
    # --header 'X-NLS-User: default' \
    # --header 'X-NLS-Token: default' \
    # 'http://nls-slp.aliyun.test:8701/api/v1/asr/vocabs'
    # 输出参数：
    # 名称 说明
    # request_id 请求 ID。
    # page 泛热词词表对象（AsrVocab）的分页结果。
    # 响应示例：
    # {
    #  "request_id": "7130914d32a3441db06747523675d9ff",
    #  "page": {
    #  "content": [
    #  {
    #  "id": "demo-vocab",
    #  "name": "示例词表",
    #  "description": "这是一个示例词表",
    #  "size": 4,
    #  "md5": "f1d3ff8443297732862df21dc4e57262",
    #  "create_time": "2018-11-01 20:11:42",
    #  "update_time": "2018-11-01 20:11:42"
    #  }
    #  ],
    #  "total_pages": 1,
    #  "total_items": 1,
    #  "page_number": 1,
    #  "page_size": 10
    #  }
    #  }
    j = {
        "request_id": "7130914d32a3441db06747523675d9ff", 
        "page": 
            {
                "total_pages": 1,
                "total_items": 1,
                "page_number": 1,
                "page_size": 10,

                "content": 
                    [
                        {"id": "demo-vocab", "name": "示例词表", "description": "这是一个示例词表", "size": 4, "md5": "f1d3ff8443297732862df21dc4e57262", "create_time": "2018-11-01 20:11:42", "update_time": "2018-11-01 20:11:42"}
                    ]
            }
        }
    
    return jsonify(j), 200

@bp.route('/api/v1/asr/vocabs/<vocab_id>', methods=['GET'])
def get_vocab(vocab_id):
    # 7.7.3.查询词表
    # 路径：
    # GET /api/v1/asr/vocabs/{vocab_id}
    # 输入参数：
    # 名称 位置 说明
    # vocab_id Path 要查询的词表 ID。
    # 请求示例：
    # curl -X GET \
    #  --header 'Accept: application/json' \
    #  --header 'X-NLS-User: default' \
    #  --header 'X-NLS-Token: default' \
    # 'http://nls-slp.aliyun.test:8701/api/v1/asr/vocabs/demo-vocab'
    # 输出参数：
    # 名称 说明
    # vocab 泛热词词表对象（AsrVocab）。
    # 响应示例：
    # {
    #  "request_id": "7130914d32a3441db06747523675d9ff",
    #  "vocab": {
    #  "id": "demo-vocab",
    #  "name": "示例词表",
    #  "description": "这是一个示例词表",
    #  "size": 4,
    #  "word_weights": {
    #  "苹果": 2,
    #  "西瓜": 3
    #  }
    #  }
    #  }
    j = {
        "request_id": "7130914d32a3441db06747523675d9ff", 
        "vocab": 
            {
                "id": "demo-vocab",
                "name": "示例词表",
                "description": "这是一个示例词表",
                "size": 4,
                "md5": "f1d3ff8443297732862df21dc4e57262",
                "create_time": "2018-11-01 20:11:42", 
                "md5": "f1d3ff8443297732862df21dc4e57262",
                "create_time": "2018-11-01 20:11:42",
                "update_time": "2018-11-01 20:11:42",
                "word_weights": {
                "苹果": 2,
                "西瓜": 3
                }
            }
        }

    return jsonify(j), 200

@bp.route('/api/v1/asr/vocabs/<vocab_id>', methods=['PUT'])
def update_vocab(vocab_id):
    # 7.7.4.更新词表
    # 路径：
    # POST /api/v1/asr/vocabs
    # 输入参数：
    # 智能语音 V2.X 【公开】 
    # 文档版本：20210430 XCVII 
    # 名称 位置 说明
    # vocab Body 类热词词表对象（AsrClassVocab）。可以设置如下参数：
    # id：词表 ID，可选，如果为空则自动生成；
    # name：词表名称；
    # description：词表描述信息，可选；
    # word_weights：要添加的词，是一个词典，键为词，值为权重。全量替换原有的词。
    # 请求示例：
    # curl -X PUT \
    #  --header 'Content-Type: application/json' \
    #  --header 'Accept: application/json' \
    #  --header 'X-NLS-User: default' \
    #  --header 'X-NLS-Token: default' \
    #  -d '{
    #  "id": "demo-vocab",
    #  "name": "示例词表（二）",
    # "description": "这是另一个示例词表",
    #  "word_weights": {"苹果": 2, "西瓜": 3}
    #  }' 'http://nls-slp.aliyun.test:8701/api/v1/asr/vocabs'
    j = request.get_json()
    print(j)
    return jsonify(j), 200


@bp.route('/api/v1/asr/vocabs/<vocab_id>', methods=['DELETE'])
def delete_vocab(vocab_id):
    # 7.7.5.删除词表
    # 路径：
    # DELETE /api/v1/asr/vocabs/{vocab_id}
    # 输入参数：
    # 名称 位置 说明
    # vocab_id Path 要删除的词表 ID。
    # 请求示例：
    # curl -X DELETE \
    #  --header 'Accept: application/json' \
    #  --header 'X-NLS-User: default' \
    #  --header 'X-NLS-Token: default' \
    #  'http://nls-slp.aliyun.test:8701/api/v1/asr/vocabs/demo-vocab'
    # 输出参数：
    # 名称 说明
    # request_id 请求 ID。
    # 响应示例：
    # {
    #  "request_id": "7130914d32a3441db06747523675d9ff"
    #  }
    j = {
        "request_id": "7130914d32a3441db06747523675d9ff"
    }

    return jsonify(j), 200