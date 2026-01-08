# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_slp_server.py 
@info: 自学习平台
"""

"""Server example using the asyncio API."""

import asyncio
from websockets.asyncio.server import serve
import json
import websockets
import uuid
import queue

import oddasr.odd_asr_config as config
from oddasr.log import logger

from oddasr.logic.odd_asr_exceptions import mai_err_name, EM_ERR_ASR_ARGS_ERROR
from oddasr.logic.odd_asr_exceptions import *
from oddasr.logic.proto import TOddAsrTranscribeRes, obj_to_dict, TOddAsrApplyRes, obj_from_dict_recursive, obj_to_dict_recursive

'''
client --> server: TCmdApppyAsrReq
server --> client: TCmdApppyAsrRsp with task_id
server --> server: add client to clients
client --> server: PCMData
server --> client: ASRResult

'''


class OddSlpServer:
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
                    self._clients_set.add(websocket)
                else:
                    '''
                    客户端已经申请过ASR，并且已经连接上了，此时收到的消息是PCMData
                    '''
                    self.onRecv(websocket, message)
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
            # if not isinstance(message, str):
            #     message = json.dumps(message)
            #     logger.debug(f"doSend: {message}")
            # else:
            #     logger.debug(f"doSend: {len(message)}")
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
        logger.debug(f"onRecv: {len(pcm_data)}, websocket={websocket}")

    def onClose(self, websocket):
        logger.info(f"Client disconnected: {websocket}")
        if websocket in self._clients_set:
            self._clients_set.remove(websocket)

            logger.info(f"remove client={websocket}")
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


def init_instances_stream(server: OddSlpServer):
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
    pass

def init_notify_task(server: OddSlpServer):
    '''
    初始化notifyTask
    :param server:
    :return:
    '''
    # notify_Task = notifyTask()
    # notify_Task.start(server)
    pass

async def start_slp_server():
    global _wss_server
    _wss_server = OddSlpServer()

    init_notify_task(_wss_server)
    init_instances_stream(_wss_server)

    async with serve(_wss_server.handle_client, config.WS_HOST, config.WS_PORT):
        await asyncio.Future()  # run forever    

if __name__ == "__main__":
    asyncio.run(start_slp_server())
