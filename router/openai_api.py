# -*- coding: utf-8 -*-
import os
import tempfile
import json

from flask import Blueprint, request, jsonify
from oddasr.log import logger
from oddasr.logic.odd_asr_instance import find_free_odd_asr_file
from oddasr.logic.odd_asr_file import OddAsrFile
from oddasr.logic.odd_asr_stream import OddAsrStream, OddAsrParamsStream
import oddasr.odd_asr_config as config

bp = Blueprint('openai', __name__, url_prefix='/v1')

odd_asr_stream_set = set()

SUPPORTED_MODELS = [
    {
        "id": "oddasr-funasr",
        "object": "model",
        "created": 1704067200,
        "owned_by": "oddmeta",
        "permission": [],
        "root": "oddasr-funasr",
        "parent": None,
        "description": "FunASR-based ASR model for Chinese speech recognition"
    },
    {
        "id": "oddasr-streaming",
        "object": "model",
        "created": 1704067200,
        "owned_by": "oddmeta",
        "permission": [],
        "root": "oddasr-streaming",
        "parent": None,
        "description": "Streaming ASR model for Chinese speech recognition"
    }
]

def find_free_odd_asr_stream():
    for odd_asr_stream in odd_asr_stream_set:
        if not odd_asr_stream.is_busy():
            return odd_asr_stream
    return None

def init_stream_instances():
    max_instance = config.odd_asr_cfg["asr_stream_cfg"]["max_instance"]
    if max_instance <= 0:
        max_instance = 1
    for i in range(max_instance):
        odd_asr_stream_param = OddAsrParamsStream(
            mode="stream",
            hotwords="",
            audio_rec_filename="",
        )
        odd_asr_stream = OddAsrStream(odd_asr_stream_param)
        odd_asr_stream_set.add(odd_asr_stream)

init_stream_instances()

SUPPORTED_FORMATS = ["json", "text", "srt", "verbose_json", "vtt"]

@bp.route('/audio/translations', methods=['POST'])
def audio_translations():
    return jsonify({"error": {"message": "audio translation not supported", "type": "invalid_request_error"}}), 400

@bp.route('/audio/transcriptions', methods=['POST'])
def audio_transcriptions():
    temp_path = None
    try:
        audio_file = request.files.get('file')
        if not audio_file:
            return jsonify({"error": {"message": "file parameter is required", "type": "invalid_request_error"}}), 400

        model = request.form.get('model', 'oddasr-funasr')
        response_format = request.form.get('response_format', 'json')
        language = request.form.get('language', '')
        prompt = request.form.get('prompt', '')
        temperature = request.form.get('temperature', 0.0)
        timestamp_granularities = request.form.get('timestamp_granularities', ['segment'])

        if model != 'oddasr-funasr':
            return jsonify({"error": {"message": f"model '{model}' not supported", "type": "invalid_request_error"}}), 400

        if response_format not in SUPPORTED_FORMATS:
            return jsonify({"error": {"message": f"response_format '{response_format}' not supported", "type": "invalid_request_error"}}), 400

        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        try:
            audio_file.save(temp_path)
            logger.info(f"Received audio and saved to: {temp_path}")
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            return jsonify({"error": {"message": f"Failed to save audio file: {str(e)}", "type": "server_error"}}), 500

        odd_asr_file: OddAsrFile = find_free_odd_asr_file()

        if not odd_asr_file:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": {"message": "no available asr instance", "type": "server_error"}}), 500

        hotwords = prompt
        try:
            if response_format in ['json', 'verbose_json']:
                asr_output_format = 'json'
            else:
                asr_output_format = response_format
            result = odd_asr_file.transcribe_file(audio_file=temp_path, hotwords=hotwords, output_format=asr_output_format)
        except Exception as e:
            logger.error(f"ASR processing error: {e}")
            return jsonify({"error": {"message": f"ASR processing error: {str(e)}", "type": "server_error"}}), 500
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"Deleted temporary file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")

        logger.info(f"Transcription completed, format={response_format}")

        if response_format == 'json':
            return jsonify({"text": result}), 200
        elif response_format == 'text':
            return result, 200, {'Content-Type': 'text/plain'}
        elif response_format == 'srt':
            return result, 200, {'Content-Type': 'text/plain'}
        elif response_format == 'verbose_json':
            return jsonify({
                "text": result,
                "segments": [],
                "language": language or "zh"
            }), 200
        elif response_format == 'vtt':
            lines = result.strip().split('\n')
            vtt_result = "WEBVTT\n\n"
            for line in lines:
                if '-->' in line:
                    vtt_result += line.replace(',', '.') + '\n'
                else:
                    vtt_result += line + '\n'
            return vtt_result, 200, {'Content-Type': 'text/vtt'}

        return jsonify({"text": result}), 200

    except Exception as e:
        logger.error(f"Unexpected error in transcriptions endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return jsonify({"error": {"message": str(e), "type": "server_error"}}), 500

@bp.route('/models', methods=['GET'])
def list_models():
    return jsonify({
        "object": "list",
        "data": SUPPORTED_MODELS
    }), 200


@bp.route('/models/<model_id>', methods=['GET'])
def retrieve_model(model_id):
    for model in SUPPORTED_MODELS:
        if model['id'] == model_id:
            return jsonify(model), 200
    return jsonify({"error": {"message": f"model '{model_id}' not found", "type": "invalid_request_error"}}), 404
