# -*- coding: utf-8 -*-
import base64
import uuid
import queue
import threading
import tempfile
import os
import wave

from flask_socketio import emit, disconnect
from flask import request
from flask import copy_current_request_context
from oddasr.log import logger

_session_audio_buffers = {}
_session_locks = {}
_session_stream_instances = {}
_result_queues = {}

def find_free_odd_asr_stream():
    from oddasr.router.openai_api import odd_asr_stream_set
    for odd_asr_stream in odd_asr_stream_set:
        if not odd_asr_stream.is_busy():
            return odd_asr_stream
    return None

def _process_audio_in_thread(session_id, audio_data, emit_func, item_id):
    try:
        temp_wav_path = None
        temp_input_path = None
        try:
            header = audio_data[:4]
            is_wav = header == b'RIFF' or header == b'WAVE'
            
            if is_wav:
                temp_wav_path = tempfile.mktemp(suffix='.wav')
                with open(temp_wav_path, 'wb') as f:
                    f.write(audio_data)
                logger.info(f"Received WAV data, size: {len(audio_data)}")
            else:
                temp_input = tempfile.NamedTemporaryFile(suffix='.webm', delete=False)
                temp_input_path = temp_input.name
                temp_input.write(audio_data)
                temp_input.close()
                
                temp_wav_path = tempfile.mktemp(suffix='.wav')
                
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(temp_input_path, format='webm')
                    audio = audio.set_frame_rate(16000).set_channels(1)
                    audio.export(temp_wav_path, format='wav')
                    logger.info(f"Converted webm to wav using pydub")
                except Exception as e:
                    logger.error(f"pydub failed: {e}, trying ffmpeg")
                    import subprocess
                    result = subprocess.run([
                        'ffmpeg', '-y', '-i', temp_input_path,
                        '-acodec', 'pcm_s16le', '-ar', '16000',
                        '-ac', '1', temp_wav_path
                    ], capture_output=True, timeout=30)
                    
                    if result.returncode != 0:
                        logger.error(f"ffmpeg also failed: {result.stderr.decode()}")
                        emit_func(f"Audio conversion failed", is_final=True, item_id=item_id)
                        return
            
            logger.info(f"Processing audio file: {temp_wav_path}, size: {len(audio_data)}")
            
            from oddasr.logic.odd_asr_instance import find_free_odd_asr_file
            odd_asr_file = find_free_odd_asr_file()
            if odd_asr_file:
                result = odd_asr_file.transcribe_file(
                    audio_file=temp_wav_path,
                    hotwords="",
                    output_format="txt"
                )
                emit_func(result, is_final=True, item_id=item_id)
                logger.info(f"Transcription result: {result}")
            else:
                emit_func("No available ASR instance", is_final=True, item_id=item_id)
                
        finally:
            if temp_input_path and os.path.exists(temp_input_path):
                try:
                    os.remove(temp_input_path)
                except:
                    pass
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except:
                    pass
                    
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        import traceback
        logger.error(traceback.format_exc())
        emit_func(f"Error: {str(e)}", is_final=True, item_id=item_id)

def init_stream_for_session(session_id):
    if session_id in _session_stream_instances:
        return _session_stream_instances[session_id]
    
    odd_asr_stream = find_free_odd_asr_stream()
    if odd_asr_stream:
        odd_asr_stream.set_busy(True)
        odd_asr_stream.set_session_id(session_id)
        _session_stream_instances[session_id] = odd_asr_stream
        return odd_asr_stream
    return None

def register_handlers(socketio):
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected to realtime API")
        session_id = str(uuid.uuid4())
        _session_audio_buffers[request.sid] = b''
        _session_locks[request.sid] = threading.Lock()
        _result_queues[request.sid] = queue.Queue()
        emit('session.created', {'id': session_id})

    @socketio.on('disconnect')
    def handle_disconnect():
        sid = request.sid
        logger.info(f"Client disconnected from realtime API: {sid}")
        
        if sid in _session_audio_buffers:
            del _session_audio_buffers[sid]
        if sid in _session_locks:
            del _session_locks[sid]
        if sid in _result_queues:
            del _result_queues[sid]
        if sid in _session_stream_instances:
            odd_asr_stream = _session_stream_instances[sid]
            odd_asr_stream.set_busy(False)
            del _session_stream_instances[sid]

    @socketio.on('session.update')
    def handle_session_update(data):
        logger.info(f"Session update: {data}")
        emit('session.updated', {'model': 'oddasr-streaming'})

    @socketio.on('input_audio_buffer.append')
    def handle_audio_append(data):
        audio_base64 = data.get('audio', '')
        if not audio_base64:
            return
        
        try:
            audio_bytes = base64.b64decode(audio_base64)
            sid = request.sid
            
            if sid not in _session_locks:
                _session_locks[sid] = threading.Lock()
            if sid not in _session_audio_buffers:
                _session_audio_buffers[sid] = b''
            
            with _session_locks[sid]:
                _session_audio_buffers[sid] += audio_bytes
            
            logger.info(f"Received audio buffer, session: {sid}, total size: {len(_session_audio_buffers.get(sid, b''))}")
            
            emit('input_audio_buffer.committed', {})
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            import traceback
            logger.error(traceback.format_exc())
            emit('error', {'error': {'type': 'server_error', 'message': str(e)}})

    @socketio.on('input_audio_buffer.commit')
    def handle_audio_commit(data):
        sid = request.sid
        logger.info(f"Commit audio buffer, session: {sid}")
        
        if sid not in _session_locks:
            _session_locks[sid] = threading.Lock()
        
        audio_data = b''
        with _session_locks[sid]:
            audio_data = _session_audio_buffers.get(sid, b'')
            _session_audio_buffers[sid] = b''
        
        if not audio_data:
            emit('error', {'error': {'type': 'invalid_request_error', 'message': 'empty audio buffer'}})
            return
        
        if len(audio_data) < 1600:
            emit('error', {'error': {'type': 'invalid_request_error', 'message': 'audio too short'}})
            return
        
        item_id = str(uuid.uuid4())
        
        emit('conversation.item.created', {
            'type': 'conversation.item.created',
            'item': {
                'id': item_id,
                'type': 'message',
                'role': 'user',
                'content': [{'type': 'input_audio', 'audio': ''}]
            }
        })
        
        def send_transcript_wrapper(text, is_final=False, item_id=item_id):
            emit('conversation.item.transcript', {
                'type': 'conversation.item.transcript',
                'item_id': item_id,
                'transcript': text,
                'is_final': is_final
            })
            if is_final:
                emit('transcript.done', {'item_id': item_id})
        
        try:
            @copy_current_request_context
            def run_process_audio():
                _process_audio_in_thread(sid, audio_data, send_transcript_wrapper, item_id)
            
            process_thread = threading.Thread(target=run_process_audio)
            process_thread.daemon = True
            process_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting audio processing: {e}")
            send_transcript_wrapper(f"Error: {str(e)}", is_final=True)

    @socketio.on('input_audio_buffer.clear')
    def handle_audio_clear(data):
        sid = request.sid
        logger.info(f"Clear audio buffer, session: {sid}")
        if sid not in _session_locks:
            _session_locks[sid] = threading.Lock()
        with _session_locks[sid]:
            _session_audio_buffers[sid] = b''
        emit('input_audio_buffer.cleared', {})

    @socketio.on('conversation.item.delete')
    def handle_item_delete(data):
        item_id = data.get('item_id', '')
        logger.info(f"Delete item: {item_id}")

    @socketio.on('message')
    def handle_message(data):
        logger.info(f"Received message: {data}")
