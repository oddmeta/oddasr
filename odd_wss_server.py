# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_wss_server.py 
@info: 消息模版
"""

"""Server example using the asyncio API."""

import asyncio
from websockets.asyncio.server import serve
import json
import numpy as np
import websockets
import ssl
import uuid
import queue
import base64
from urllib.parse import urlparse, parse_qs

import torch
import torchaudio

from odd_asr_stream import OddAsrStream, OddAsrParamsStream
from odd_asr_result import notifyTask, set_openai_result_callback
from odd_asr_instance import InstancePool
import odd_asr_config as config
from log import logger
from odd_asr_exceptions import *
from proto import TOddAsrTranscribeRes, obj_to_dict, TOddAsrApplyRes, obj_from_dict_recursive, obj_to_dict_recursive

'''
client --> server: TCmdApppyAsrReq
server --> client: TCmdApppyAsrRsp with task_id
server --> server: add client to clients
client --> server: PCMData
server --> client: ASRResult

'''


odd_asr_stream_pool = InstancePool()
_wss_server = None

# ============================================================
# OpenAI 兼容实时转录相关
# ============================================================

# OpenAI 连接追踪：websocket -> session info dict
openai_connections = {}

def _build_ulaw_decode_table():
    """构建 G.711 u-law 解码查找表（Sun Microsystems 算法）"""
    table = []
    for i in range(256):
        ulaw = ~i & 0xFF
        t = ((ulaw & 0x0F) << 3) + 0x84
        t <<= (ulaw & 0x70) >> 4
        if ulaw & 0x80:
            table.append(0x84 - t)
        else:
            table.append(t - 0x84)
    return table

_ULAW_TABLE_NP = np.array(_build_ulaw_decode_table(), dtype=np.int16)


def _validate_openai_token(websocket):
    """从 websocket 请求中提取并验证 Bearer Token"""
    api_key = config.openai_api_key
    if not api_key:
        return True  # 空 key 表示不鉴权

    token = None

    # 从 Authorization header 提取
    if hasattr(websocket, 'request') and hasattr(websocket.request, 'headers'):
        auth_header = websocket.request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

    # 从 query 参数提取
    if not token and hasattr(websocket, 'request'):
        parsed = urlparse(websocket.request.path)
        params = parse_qs(parsed.query)
        token = params.get('token', [None])[0] or params.get('api_key', [None])[0]

    if not token:
        return False

    if isinstance(api_key, str):
        return token == api_key
    elif isinstance(api_key, list):
        return token in api_key
    return False


async def _openai_result_handler(message, wss_server):
    """处理 OpenAI 连接的转录结果，返回 True 表示已处理"""
    ws = message.webocket
    if ws not in openai_connections:
        return False

    info = openai_connections[ws]
    text = message.res.payload.result
    is_final = message.res.header.name == "SentenceEnd"
    is_last = message.res.payload.fin == 1

    # 转写结束信号
    if is_last and text == "END":
        return True

    # 连接已关闭，丢弃结果
    if text is None:
        return True

    event_id = f"evt_{uuid.uuid1().hex[:24]}"

    if is_final:
        event = {
            "type": "conversation.item.input_audio_transcription.completed",
            "event_id": event_id,
            "item_id": info["session_id"],
            "transcript": text,
        }
    else:
        event = {
            "type": "conversation.item.input_audio_transcription.delta",
            "event_id": event_id,
            "item_id": info["session_id"],
            "delta": text,
        }

    await wss_server.doSend(ws, json.dumps(event))
    return True

def find_free_odd_asr_stream(websocket, task_id):
    '''
    从实例池获取一个空闲的odd_asr_stream
    :param websocket:
    :param task_id:
    :return:
    '''
    stream = odd_asr_stream_pool.acquire()
    if stream:
        stream.set_busy(True)
        stream.set_session_id(task_id)
        stream.set_websocket(websocket)
    return stream

def find_odd_asr_stream_by_websocket(websocket):
    '''
    找到websocket对应的odd_asr_stream
    :param websocket:
    :return:
    '''
    return odd_asr_stream_pool.find_by_websocket(
        lambda s: s.get_websocket(), websocket
    )

def free_odd_asr_stream(odd_asr_stream):
    '''
    释放一个odd_asr_stream回实例池
    :param odd_asr_stream:
    :return:
    '''
    odd_asr_stream.set_busy(False)
    odd_asr_stream.set_session_id(None)
    odd_asr_stream.set_websocket(None)
    odd_asr_stream_pool.release(odd_asr_stream)

def find_odd_asr_stream_by_session_id(task_id):
    '''
    找到一个已存在的odd_asr_stream
    :param task_id:
    :return:
    '''
    return odd_asr_stream_pool.find_by_session_id(
        lambda s: s.get_session_id(), task_id
    )

class OddWssServer:
    def __init__(self):
        self._clients_set = set()
        self._sessionid_set = set()
        self._conn_sessionid = dict()
        self._sessionid_conn = dict()

    async def handle_client(self, *args, **kwargs):
        # 从参数中提取 websocket 和 path
        websocket = args[0]
        logger.debug(f"Client connected: {websocket}, args={args}, len={len(args)}, kwargs={kwargs}")

        # 检查是否为 OpenAI 实时转录路径
        path = '/'
        if hasattr(websocket, 'request') and hasattr(websocket.request, 'path'):
            path = websocket.request.path

        parsed = urlparse(path)
        if parsed.path == '/v1/realtime':
            params = parse_qs(parsed.query)
            intent = params.get('intent', [''])[0]
            if intent != 'transcription':
                await websocket.close(code=4003, reason='Invalid intent')
                return
            await self.handle_openai_realtime(websocket)
            return
        
        try:
            async for message in websocket:
                if not websocket in self._clients_set:
                    '''
                    新连接上来的client，第一个消息必须是一个json.
                    namespace: SpeechTranscriber
                    name: StartTranscription
                    message_id: 消息id
                    token: 鉴权token
                    task_id: 正常第一次连接为空，Apply成功后，由服务端生成并返回给客户端。客户端断线重连的时候带上。
                    '''
                    result, res, task_id = self.doInit(websocket, message)

                    logger.info(f"doInit={result}, res={obj_to_dict_recursive(res)}, websocket={websocket}, task_id={task_id}")

                    await websocket.send(json.dumps(obj_to_dict_recursive(res)))

                    if result:
                        logger.debug(f"add client={websocket} to clients_set")
                    else:
                        logger.error(f"doInit failed, close client={websocket}")
                        await websocket.close()
                        return False

                    # find a odd_asr_stream
                    odd_asr_stream:OddAsrStream = find_odd_asr_stream_by_session_id(task_id=task_id)
                    if odd_asr_stream is None:
                        odd_asr_stream = find_free_odd_asr_stream(websocket, task_id)
                        if odd_asr_stream is None:
                            logger.error(f"no free odd_asr_stream, close client={websocket}")
                            await websocket.close()
                            return
                        else:
                            logger.debug(f"found free odd_asr_stream, task_id={task_id}")
                            self._sessionid_set.add(task_id)
                    else:
                        logger.info(f"found existing odd_asr_stream, task_id={task_id}, websocket={odd_asr_stream.get_websocket()}:{websocket}")

                    self._clients_set.add(websocket)
                    self._conn_sessionid[websocket] = task_id
                    self._sessionid_conn[task_id] = websocket
                else:
                    '''
                    客户端已经申请过ASR，并且已经连接上了，此时收到的消息是PCMData
                    '''
                    if type(message) is bytes:
                        self.onRecv(websocket, message)
                    else:
                        # {'service_type':'ASR','msg_type':'STOP_SESSION_REQ'}
                        self.doCtrl(websocket, message)
                        logger.error(f"invalid message type, {type(message)}, {message}")

                    continue

        finally:
            self.onClose(websocket)

    async def handle_openai_realtime(self, websocket):
        """处理 OpenAI 实时转录 WebSocket 连接"""
        # 验证认证
        if not _validate_openai_token(websocket):
            await websocket.close(code=4001, reason='Invalid authentication')
            return

        session_id = str(uuid.uuid1())

        # 查找空闲的 stream 实例
        stream = find_free_odd_asr_stream(websocket, session_id)
        if stream is None:
            logger.error("no free odd_asr_stream for OpenAI client")
            await websocket.close(code=4002, reason='No available ASR instance')
            return

        # 创建 OpenAI 会话信息
        resampler = torchaudio.transforms.Resample(8000, 16000)
        openai_connections[websocket] = {
            "session_id": session_id,
            "stream": stream,
            "resampler": resampler,
        }

        # 注册到服务器客户端集合
        self._clients_set.add(websocket)
        self._conn_sessionid[websocket] = session_id
        self._sessionid_conn[session_id] = websocket
        self._sessionid_set.add(session_id)

        try:
            # 发送 transcription_session.created
            await self._send_openai_event(websocket, {
                "type": "transcription_session.created",
                "session": {
                    "id": session_id,
                    "input_audio_format": "g711_ulaw",
                    "input_audio_sample_rate": 8000,
                }
            })

            # 消息循环
            async for message in websocket:
                if isinstance(message, bytes):
                    continue  # OpenAI 使用 JSON 事件，忽略裸 bytes

                try:
                    event = json.loads(message)
                    event_type = event.get('type', '')

                    match event_type:
                        case 'transcription_session.update':
                            await self._handle_openai_session_update(websocket, event)
                        case 'input_audio_buffer.append':
                            await self._handle_openai_audio_append(websocket, event)
                        case 'input_audio_buffer.commit':
                            await self._handle_openai_audio_commit(websocket)
                        case 'input_audio_buffer.clear':
                            pass  # 暂不实现
                        case _:
                            logger.warning(f"Unknown OpenAI event: {event_type}")

                except json.JSONDecodeError:
                    logger.error("Invalid JSON from OpenAI client")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"OpenAI client disconnected: {session_id}")
        finally:
            # 清理 OpenAI 连接
            if websocket in openai_connections:
                del openai_connections[websocket]
            free_odd_asr_stream(stream)
            self.onClose(websocket)

    async def _send_openai_event(self, websocket, event):
        """发送 OpenAI 格式事件"""
        if 'event_id' not in event:
            event['event_id'] = f"evt_{uuid.uuid1().hex[:24]}"
        await websocket.send(json.dumps(event))

    async def _handle_openai_session_update(self, websocket, event):
        """处理 transcription_session.update 事件"""
        info = openai_connections.get(websocket)
        if not info:
            return

        await self._send_openai_event(websocket, {
            "type": "transcription_session.updated",
            "session": {
                "id": info["session_id"],
                "input_audio_format": "g711_ulaw",
                "input_audio_sample_rate": 8000,
            }
        })

    async def _handle_openai_audio_append(self, websocket, event):
        """处理 input_audio_buffer.append 事件"""
        info = openai_connections.get(websocket)
        if not info:
            return

        audio_base64 = event.get('audio', '')
        if not audio_base64:
            return

        try:
            # base64 解码 → u-law → PCM16 → 重采样 8kHz→16kHz
            ulaw_bytes = base64.b64decode(audio_base64)
            pcm16 = _ULAW_TABLE_NP[np.frombuffer(ulaw_bytes, dtype=np.uint8)]

            pcm_tensor = torch.tensor(pcm16, dtype=torch.float32).unsqueeze(0)
            resampled = info["resampler"](pcm_tensor).squeeze(0)
            pcm_resampled = resampled.numpy().astype(np.int16)

            # 送入流式 ASR
            info["stream"].transcribe_stream(
                pcm_resampled.tobytes(),
                socket=websocket,
                task_id=info["session_id"]
            )

        except Exception as e:
            logger.error(f"Error processing OpenAI audio: {e}")

    async def _handle_openai_audio_commit(self, websocket):
        """处理 input_audio_buffer.commit 事件"""
        info = openai_connections.get(websocket)
        if info and info["stream"]:
            # 发送 EOF 触发最终结果
            info["stream"].transcribe_stream(
                None, socket=websocket, task_id=info["session_id"]
            )

    async def doSend(self, websocket, message):
        '''
        发送消息给客户端
        :param websocket:
        :param message:
        :return:
        '''
        try:
            if not isinstance(message, str):
                message = json.dumps(message)
                logger.debug(f"doSend: {message}")
            else:
                logger.debug(f"doSend: {len(message)}")
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosedOK:
            logger.error(f"Connection closed normally: {websocket}")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed with error: {e}, {websocket}")
        except Exception as e:
            logger.error(f"Unexpected error in doSend: {e}, {websocket}")

    async def doBroadcast(self, message):
        for client in self._clients_set:
            await client.send(message)

    def onRecv(self, websocket, pcm_data):
        # logger.debug(f"onRecv: {len(pcm_data)}, websocket={websocket}")

        # 找到对应的odd_asr_stream
        task_id = ""
        odd_asr_stream: OddAsrStream = find_odd_asr_stream_by_websocket(websocket=websocket)
        if odd_asr_stream:
            task_id = odd_asr_stream.get_session_id()
            # logger.debug(f"find_odd_asr_stream_by_websocket, task_id={task_id}")
            odd_asr_stream.transcribe_stream(pcm_data, socket=websocket, task_id=task_id)
        else:
            logger.error(f"find_odd_asr_stream_by_websocket, not found, websocket={websocket}")

    def onClose(self, websocket):
        logger.warn(f"Client disconnected: {websocket}")
        if websocket in self._clients_set:
            '''
            客户端断开连接，需要从clients中删除。
            然而暂不在sessionid_set中删除，因为可能是客户端断线重连，此时sessionid还存在。
            但是，后面需要做一个计时器，定期检查，若超时未收到客户端的消息，则删除sessionid。
            '''
            task_id = self._conn_sessionid[websocket]

            # self._sessionid_set.remove(task_id)
            self._sessionid_conn.pop(task_id)
            self._conn_sessionid.pop(websocket)
            self._clients_set.remove(websocket)
            odd_asr_stream = find_odd_asr_stream_by_session_id(task_id=task_id)

            # logger.warn(f"remove task_id={task_id}, client={websocket}, odd_asr_stream={odd_asr_stream}")

            if odd_asr_stream:
                free_odd_asr_stream(odd_asr_stream)

            logger.warn(f"remove task_id={task_id}, client={websocket}")
        else:
            logger.error(f"client={websocket} not in clients_set")

    def doInit(self, websocket, message):
        # 解析json，若第一个消息不是json，则关闭连接
        result = False
        try:
            req = json.loads(message)
        except Exception as e:
            logger.error(f"Invalid json format. Received message: {message}. webocket={websocket}")
            message_id = ''
            name = ''

            res = TOddAsrApplyRes()
            res.header.message_id = message_id
            res.header.name = name
            res.header.status = EM_ERR_ASR_ARGS_ERROR
            res.header.status_text = mai_err_name(EM_ERR_ASR_ARGS_ERROR)

            return result, res, ""

        # 解析json中的session_id
        res = TOddAsrApplyRes()
        res.header.message_id = req['message_id'] if 'message_id' in req else ''
        res.header.task_id = req['task_id'] if 'task_id' in req else ''
        res.header.name = req['name'] if 'name' in req else ''

        # 若第一个消息不是StartTranscription，则关闭连接
        if req['name'] != 'StartTranscription':
            logger.error(f"Invalid name. Received message: {message}, req['name']")
            res.header.status = EM_ERR_ASR_ARGS_ERROR
            res.header.status_text = mai_err_name(EM_ERR_ASR_ARGS_ERROR)

            return result, res, res.header.task_id

        if "task_id" in req and req['task_id']:
            if req['task_id'] in self._sessionid_set:
                '''若task_id已经存在，说明是之前已经申请过ASR，但是中间网络异常，并断线重连了
                '''
                self._sessionid_conn[req['task_id']] = websocket
                self._conn_sessionid[websocket] = req['task_id']

                res.header.status = 0
                res.header.status_text = "Success"

                result = True
            else:
                '''
                若task_id不存在，说明是一个非法请求
                '''
                logger.error(f"Received message: {message}, req['task_id']={req['task_id']}")
                res.header.status  = EM_ERR_ASR_SESSION_ID_NOVALID
                res.header.status_text = mai_err_name(EM_ERR_ASR_SESSION_ID_NOVALID)
                result = False
        else:
            '''
            若task_id为空，说明是第一次申请ASR，需要生成一个task_id
            '''
            res.header.task_id = str(uuid.uuid1())
            res.header.name = "SentenceBegin"
            res.header.status = 0

            self._sessionid_set.add(res.header.task_id)
            self._sessionid_conn[res.header.task_id] = websocket
            self._conn_sessionid[websocket] = res.header.task_id

            result = True

        return result, res, res.header.task_id

    def doCtrl(self, websocket, message):
        # 解析json，若第一个消息不是json，则关闭连接
        result = False
        try:
            req = json.loads(message)
        except Exception as e:
            logger.error(f"Invalid json format. Received message: {message}. webocket={websocket}")
            message_id = ''
            name = ''

            res = TOddAsrApplyRes()
            res.header.message_id = message_id
            res.header.name = name
            res.header.status = EM_ERR_ASR_ARGS_ERROR
            res.header.status_text = mai_err_name(EM_ERR_ASR_ARGS_ERROR)

            return result, res, ""

        # 解析json中的session_id
        name_value = req.get('name', '')
        task_id = req.get('task_id', '')
        message_id = req.get('message_id', '')

        logger.warn(f"Received message: {message}, name={name_value}, task_id={task_id}, message_id={message_id}")

        res = TOddAsrApplyRes()
        res.header.message_id = message_id
        res.header.task_id = task_id
        res.header.name = name_value

        # 若消息不是STOP_SESSION_REQ
        if name_value != 'STOP_SESSION_REQ':
            logger.error(f"Invalid name. Received message: {message}, req['name']={name_value}")
            res.header.status = EM_ERR_ASR_ARGS_ERROR
            res.header.status_text = mai_err_name(EM_ERR_ASR_ARGS_ERROR)

            return result, res, res.header.task_id
        
        odd_asr_stream = find_odd_asr_stream_by_session_id(task_id=task_id)
        if not odd_asr_stream:
            logger.error(f"task_id={task_id} not found")
            res.header.status = EM_ERR_ASR_SESSION_ID_NOVALID
            res.header.status_text = mai_err_name(EM_ERR_ASR_SESSION_ID_NOVALID)
            return result, res, res.header.task_id
        else:
            if task_id in self._sessionid_set:
                self._sessionid_conn[task_id] = None

            self._conn_sessionid[websocket] = None
            res.header.status = 0
            res.header.status_text = "Success"


        result = True

        return result, res, res.header.task_id


    async def send(self, websocket, message):
        await websocket.send(message)

async def notify_task(_wss_server=None):
    global asr_result_queue
    while True:
        try:
            # 使用 asyncio.to_thread 从队列获取消息
            message = await asyncio.to_thread(asr_result_queue.get, timeout=1)
            logger.debug(f"notifyTask: {message.text}")

            if _wss_server:
                if message.webocket in _wss_server._clients_set:
                    # 发送消息给客户端
                    res = TOddAsrTranscribeRes()
                    res.header.message_id = message.message_id
                    res.header.name = message.name
                    res.header.status = message.status
                    res.header.status_text = message.status_text
                    res.payload = message.payload
                    message.text = json.dumps(obj_to_dict_recursive(res))
                    
                    logger.debug(f"notifyTask: send to client={message.webocket}, message.text={message.text}")
                    await _wss_server.doSend(message.webocket, message.text)
        except queue.Empty:
            # 队列为空，继续等待
            continue
        except Exception as e:
            # 处理其他异常
            logger.error(f"notifyTask error: {e}")
            continue


def init_instances_stream(server: OddWssServer):
    '''
    初始化odd_asr_stream实例。
    由于初始化加载模型比较耗时，所以在启动的时候就预加载。
    电脑内存太小，默认这里只初始化2个实例。
    每个odd_asr_stream实例对应一个websocket连接。
    每个websocket连接对应一个odd_asr_stream实例。
    每个odd_asr_stream实例对应一个session_id。
    每个session_id对应一个websocket连接。
    每个websocket连接对应一个session_id。
    每个session_id对应一个odd_asr_stream实例。
    :param server:
    :return:
    '''
    max_instance = config.odd_asr_cfg["asr_stream_cfg"]["max_instance"]

    if max_instance <= 0:
        max_instance = 1

    for i in range(max_instance):
        odd_asr_stream_param: OddAsrParamsStream = OddAsrParamsStream(
            mode="stream",
            hotwords="",
            audio_rec_filename="",
        )
        odd_asr_stream = OddAsrStream(odd_asr_stream_param)
        odd_asr_stream_pool.add(odd_asr_stream)

def init_notify_task(server: OddWssServer):
    '''
    初始化notifyTask
    :param server:
    :return:
    '''
    notify_Task = notifyTask()
    notify_Task.start(server)


async def start_wss_server():
    global _wss_server
    _wss_server = OddWssServer()

    # 注册 OpenAI 结果处理回调
    set_openai_result_callback(_openai_result_handler)

    init_notify_task(_wss_server)
    init_instances_stream(_wss_server)

    # Configure SSL context if HTTPS is enabled
    ssl_context = None
    if config.odd_asr_cfg["enable_https"]:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(
            config.odd_asr_cfg["ssl_cert_path"],
            config.odd_asr_cfg["ssl_key_path"]
        )
    
    async with serve(_wss_server.handle_client, config.WS_HOST, config.WS_PORT, ssl=ssl_context):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(start_wss_server())
