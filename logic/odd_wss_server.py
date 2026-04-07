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

import oddasr.odd_asr_config as config
from oddasr.log import logger

from oddasr.logic.odd_asr_stream import OddAsrStream, OddAsrParamsStream
from oddasr.logic.odd_asr_result import notifyTask
from oddasr.logic.odd_asr_exceptions import *
from oddasr.logic.proto import TOddAsrTranscribeRes, obj_to_dict, TOddAsrApplyRes, obj_from_dict_recursive, obj_to_dict_recursive

'''
client --> server: TCmdApppyAsrReq
server --> client: TCmdApppyAsrRsp with task_id
server --> server: add client to clients
client --> server: PCMData
server --> client: ASRResult

'''


odd_asr_stream_set = set()
_wss_server = None

def find_free_odd_asr_stream(websocket, task_id):
    '''
    找到一个空闲的odd_asr_stream
    :param websocket:
    :return:
    '''
    for odd_asr_stream in odd_asr_stream_set:
        if not odd_asr_stream.is_busy():
            odd_asr_stream.set_busy(True)
            odd_asr_stream.set_session_id(task_id)
            odd_asr_stream.set_websocket(websocket)

            return odd_asr_stream
        
    return None

def find_odd_asr_stream_by_websocket(websocket):
    '''
    找到websocket对应的odd_asr_stream
    :param websocket:
    :return:
    '''
    for odd_asr_stream in odd_asr_stream_set:
        if odd_asr_stream.get_websocket() == websocket:
            return odd_asr_stream
        
    return None

def free_odd_asr_stream(odd_asr_stream):
    '''
    释放一个odd_asr_stream
    :param odd_asr_stream:
    :return:
    '''
    odd_asr_stream.set_busy(False)
    odd_asr_stream.set_session_id(None)
    odd_asr_stream.set_websocket(None)

def find_odd_asr_stream_by_session_id(task_id):
    '''
    找到一个已存在的odd_asr_stream
    :param task_id:
    :return:
    '''
    for odd_asr_stream in odd_asr_stream_set:
        if odd_asr_stream.get_session_id() == task_id:
            return odd_asr_stream
    return None

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
                odd_asr_stream.set_websocket(None)
                odd_asr_stream.set_busy(False)
                # odd_asr_stream.set_session_id('')

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


def init_instances_stream(server: OddWssServer = None):
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
            # result_callback=server.doSend,
        )
        odd_asr_stream = OddAsrStream(odd_asr_stream_param)
        odd_asr_stream_set.add(odd_asr_stream)

def init_notify_task(server: OddWssServer):
    '''
    初始化notifyTask
    :param server:
    :return:
    '''
    notify_Task = notifyTask()
    notify_Task.start(server)


# 修改 oddasr/logic/odd_wss_server.py 文件中的 start_wss_server 函数
async def start_wss_server():
    global _wss_server
    _wss_server = OddWssServer()
    
    ssl_context = None
    if config.odd_asr_cfg["enable_https"]:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(
            config.odd_asr_cfg["ssl_cert_path"],
            config.odd_asr_cfg["ssl_key_path"]
        )
    
    # 创建服务器
    server = await serve(_wss_server.handle_client, config.WS_HOST, config.WS_PORT, ssl=ssl_context)
    
    try:
        # 等待取消
        await asyncio.Future()
    except asyncio.CancelledError:
        # 关闭服务器
        server.close()
        await server.wait_closed()
        logger.info("WebSocket server closed")
        raise

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