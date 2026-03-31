# -*- coding: utf-8 -*-
import base64
import uuid
import queue
import threading
import time
import numpy as np

from flask_socketio import emit, disconnect
from flask import request
from flask import copy_current_request_context
from oddasr.log import logger
from oddasr.logic.odd_asr_result import asr_result_queue

_session_stream_instances = {}
_session_locks = {}
_session_start_time = {}
_result_dispatch_thread = None
_dispatch_running = False

def find_free_odd_asr_stream():
    from oddasr.router.openai_api import odd_asr_stream_set
    for odd_asr_stream in odd_asr_stream_set:
        if not odd_asr_stream.is_busy():
            return odd_asr_stream
    return None

def init_stream_for_session(sid):
    if sid in _session_stream_instances:
        return _session_stream_instances[sid]
    
    odd_asr_stream = find_free_odd_asr_stream()
    if odd_asr_stream:
        odd_asr_stream.set_busy(True)
        odd_asr_stream.set_session_id(sid)
        _session_stream_instances[sid] = odd_asr_stream
        _session_start_time[sid] = time.time()
        return odd_asr_stream
    return None

def release_stream_for_session(sid):
    if sid in _session_stream_instances:
        odd_asr_stream = _session_stream_instances[sid]
        odd_asr_stream.set_busy(False)
        odd_asr_stream.set_session_id(None)
        del _session_stream_instances[sid]
    if sid in _session_start_time:
        del _session_start_time[sid]

def dispatch_results(socketio):
    global _dispatch_running
    while _dispatch_running:
        try:
            if not asr_result_queue.empty():
                result = asr_result_queue.get_nowait()
                
                if result and result.res.payload.result:
                    session_id = result.webocket
                    
                    text = result.res.payload.result
                    is_final = result.res.payload.fin == 1
                    
                    item_id = str(uuid.uuid4())
                    
                    socketio.emit('conversation.item.transcript', {
                        'type': 'conversation.item.transcript',
                        'item_id': item_id,
                        'transcript': text,
                        'is_final': is_final
                    }, room=session_id)
                    
                    if is_final:
                        socketio.emit('transcript.done', {'item_id': item_id}, room=session_id)
                        
            time.sleep(0.05)
        except queue.Empty:
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error dispatching results: {e}")
            time.sleep(0.1)

def start_result_dispatch(socketio):
    global _dispatch_running, _result_dispatch_thread
    if not _dispatch_running:
        _dispatch_running = True
        _result_dispatch_thread = threading.Thread(target=dispatch_results, args=(socketio,), daemon=True)
        _result_dispatch_thread.start()
        logger.info("ASR result dispatch thread started")

def process_audio_stream(sid, audio_bytes):
    if sid not in _session_stream_instances:
        init_stream_for_session(sid)
    
    odd_asr_stream = _session_stream_instances.get(sid)
    if not odd_asr_stream:
        logger.error(f"No stream instance for session {sid}")
        return
    
    if len(audio_bytes) % 2 != 0:
        audio_bytes = audio_bytes[:-1]
    
    item_id = str(uuid.uuid4())
    
    try:
        odd_asr_stream.transcribe_stream(audio_bytes, sid, item_id)
    except Exception as e:
        logger.error(f"Error in stream transcription: {e}")
        import traceback
        logger.error(traceback.format_exc())

def register_handlers(socketio):
    start_result_dispatch(socketio)
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected to realtime API")
        session_id = str(uuid.uuid4())
        init_stream_for_session(request.sid)
        emit('session.created', {'id': session_id})

    @socketio.on('disconnect')
    def handle_disconnect():
        sid = request.sid
        logger.info(f"Client disconnected from realtime API: {sid}")
        release_stream_for_session(sid)

    @socketio.on('session.update')
    def handle_session_update(data):
        logger.info(f"Session update: {data}")
        init_stream_for_session(request.sid)
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
            
            with _session_locks[sid]:
                process_audio_stream(sid, audio_bytes)
            
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
        
        odd_asr_stream = _session_stream_instances.get(sid)
        if odd_asr_stream and hasattr(odd_asr_stream, 'streamParam'):
            try:
                if odd_asr_stream.streamParam._audio_queue is not None:
                    eof_frame = b''
                    odd_asr_stream.transcribe_stream(eof_frame, sid, str(uuid.uuid4()))
            except Exception as e:
                logger.error(f"Error ending stream: {e}")
        
        emit('input_audio_buffer.committed', {})

    @socketio.on('input_audio_buffer.clear')
    def handle_audio_clear(data):
        sid = request.sid
        logger.info(f"Clear audio buffer, session: {sid}")
        
        release_stream_for_session(sid)
        init_stream_for_session(sid)
        
        emit('input_audio_buffer.cleared', {})

    @socketio.on('conversation.item.delete')
    def handle_item_delete(data):
        item_id = data.get('item_id', '')
        logger.info(f"Delete item: {item_id}")

    @socketio.on('message')
    def handle_message(data):
        logger.info(f"Received message: {data}")