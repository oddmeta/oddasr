# -*- coding: utf-8 -*-
"""
@author: pinghe
@contact: pinghe@oddmeta.com
@software: PyCharm
@file: openai_api.py
@info: OpenAI 兼容 ASR 端点
"""

import os
import time
import functools
import tempfile

import soundfile as sf

from flask import Blueprint, request, jsonify

from log import logger
from odd_asr_instance import find_free_odd_asr_sentence, release_odd_asr_sentence
import odd_asr_config as config

bp = Blueprint('openai_asr', __name__, url_prefix='')


def _check_api_key():
    """检查 OpenAI API Key 是否匹配"""
    api_key = config.openai_api_key
    if not api_key:
        return True  # 空 key 表示不鉴权

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False

    token = auth_header[7:]
    if isinstance(api_key, str):
        return token == api_key
    elif isinstance(api_key, list):
        return token in api_key
    return False


def _openai_auth_error():
    """返回 OpenAI 格式的认证错误"""
    return jsonify({
        "error": {
            "message": "Invalid authentication",
            "type": "invalid_request_error",
            "code": "invalid_api_key"
        }
    }), 401


def openai_auth_required(f):
    """OpenAI API 鉴权装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not _check_api_key():
            return _openai_auth_error()
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/v1/audio/transcriptions', methods=['POST'])
@openai_auth_required
def transcribe():
    """
    OpenAI 兼容的音频转录端点
    接受 multipart/form-data，字段：file（必需）、model、language、prompt
    """
    try:
        audio_file = request.files.get('file')
        if not audio_file:
            return jsonify({
                "error": {
                    "message": "No audio file provided",
                    "type": "invalid_request_error"
                }
            }), 400

        # 检查文件大小（限制 100MB）
        audio_file.seek(0, 2)
        file_size = audio_file.tell()
        audio_file.seek(0)
        if file_size > 100 * 1024 * 1024:
            return jsonify({
                "error": {
                    "message": "File size exceeds 100MB limit",
                    "type": "invalid_request_error"
                }
            }), 400

        # model 和 language 参数忽略，使用现有模型
        # prompt 可作为热词使用
        prompt = request.form.get('prompt', '')

        # 保存上传文件到临时位置
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"openai_audio_{os.urandom(8).hex()}")
        try:
            audio_file.save(temp_path)
            logger.info(f"OpenAI API: received audio, saved to {temp_path}")
        except Exception as e:
            logger.error(f"OpenAI API: failed to save audio file: {e}")
            return jsonify({
                "error": {
                    "message": f"Failed to save audio file: {str(e)}",
                    "type": "server_error"
                }
            }), 500

        # 获取 ASR 实例
        odd_asr_sentence = find_free_odd_asr_sentence()
        if not odd_asr_sentence:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({
                "error": {
                    "message": "No available ASR instance",
                    "type": "server_error"
                }
            }), 503

        try:
            # 调用现有 sentence ASR 进行转写
            result = odd_asr_sentence.transcribe_sentence(
                audio_file=temp_path,
                hotwords=prompt,
                output_format="txt"
            )

            # 计算音频时长（仅读 metadata，不解码音频数据）
            duration = 0.0
            try:
                info = sf.info(temp_path)
                duration = info.duration
            except Exception:
                pass

            response = {
                "task": "transcribe",
                "language": "zh",
                "duration": round(duration, 2),
                "text": result if result else ""
            }

            logger.info(f"OpenAI API: transcription result length={len(result) if result else 0}")
            return jsonify(response), 200

        except Exception as e:
            logger.error(f"OpenAI API: ASR processing error: {e}")
            return jsonify({
                "error": {
                    "message": f"ASR processing error: {str(e)}",
                    "type": "server_error"
                }
            }), 500
        finally:
            release_odd_asr_sentence(odd_asr_sentence)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

    except Exception as e:
        logger.error(f"OpenAI API: unexpected error: {e}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "server_error"
            }
        }), 500
