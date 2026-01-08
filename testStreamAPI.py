# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: testStreamAPI.py 
@info: 消息模版
"""

"""Client example using the asyncio API."""

'''
    client --> server: connect
    client --> server: TCmdApppyAsrReq, msg_type = StartTranscription;
    server --> client: TCmdApplyAsrRes, msg_type = MSG_SUBSCRIBE_INIT_RES;
    client --> server: TCMDTranscribeReq, msg_type = MSG_TRANSCRIBE_REQ;
    server --> client: TCMDTranscribeRes, msg_type = MSG_TRANSCRIBE_RES;

    TCMDTranscribeReq

'''

import asyncio
import json
import time
import websockets
import enum

from websockets.asyncio.client import connect

from oddasr.log import logger
import oddasr.odd_asr_config as config
import oddasr.logic.proto as proto

class odd_asr_state(enum.Enum):
    EM_ASR_STATE_IDLE = 0,
    EM_ASR_STATE_APPLYING = 1,
    EM_ASR_STATE_APLLY_OK = 2,
    EM_ASR_STATE_APPLY_FAILED = 3,
    EM_ASR_STATE_RECOGNIZING = 4,

# state: odd_asr_state = odd_asr_state.EM_ASR_STATE_IDLE

class OddWsClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.state = odd_asr_state.EM_ASR_STATE_IDLE
        self.timestamp_apply = 0
        self.timestamp_first_packet = 0
        self.timestamp_first_text = 0
        self.timestamp_last_packet = 0
        self.timestamp_last_text = 0
        self.timestamp_sentence_begin = 0
        self.timestamp_sentence_end = 0

ws_client_set = set()


async def receive_messages(websocket):
    '''
    receive message from server
    :param websocket: WebSocket connection object
    '''

    while True:
        try:
            # 接收服务端消息
            message = await websocket.recv()
            # logger.debug(f"<<< {message}")

            odd_ws_client: OddWsClient = None
            for client in ws_client_set:
                if client.websocket == websocket:
                    odd_ws_client = client

            match odd_ws_client.state:
                case odd_asr_state.EM_ASR_STATE_IDLE:
                    continue
                case odd_asr_state.EM_ASR_STATE_APPLYING:
                    response = json.loads(message)
                    logger.debug(f"<<< {response}")
                    res = proto.TOddAsrApplyRes()
                    res = proto.obj_from_dict_recursive(res, response)
                    if res.header.name == "SentenceBegin":
                        if res.header.status == 0:
                            odd_ws_client.state = odd_asr_state.EM_ASR_STATE_APLLY_OK
                            logger.info("client doInit ok")
                            odd_ws_client.state = odd_asr_state.EM_ASR_STATE_RECOGNIZING
                            odd_ws_client.timestamp_first_text = time.time()
                            odd_ws_client.timestamp_sentence_begin = res.payload.time
                        else:
                            odd_ws_client.state = odd_asr_state.EM_ASR_STATE_APPLY_FAILED
                    odd_ws_client.timestamp_apply = time.time()
                    continue
                case odd_asr_state.EM_ASR_STATE_APLLY_OK:
                    continue
                case odd_asr_state.EM_ASR_STATE_APPLY_FAILED:
                    continue
                case odd_asr_state.EM_ASR_STATE_RECOGNIZING:
                    response = json.loads(message)
                    logger.debug(f"<<< {response}")
                    res = proto.TOddAsrTranscribeRes()
                    res = proto.obj_from_dict_recursive(res, response)
                    if res.header.name == "SentenceEnd":
                        odd_ws_client.timestamp_sentence_end = time.time()
                    elif res.header.name == "SentenceBegin":
                        odd_ws_client.timestamp_sentence_begin = res.payload.time
                    elif res.header.name == "TranscriptionResultChanged":
                        odd_ws_client.timestamp_last_packet = time.time()
                    elif res.header.name == "TranscriptionCompleted":
                        odd_ws_client.timestamp_last_text = time.time()
                    else:
                        logger.error(f"unknown message type={res.header.name}")
                case _:
                    continue

        except websockets.exceptions.ConnectionClosedOK:
            logger.error("Connection closed gracefully")
            break
        except Exception as e:
            logger.error(f"Receive error: {e}")
            break

async def send_messages(websocket, file):
    offset = 0
    total_length = 0
    chunk_size = 9600*2

    odd_ws_client: OddWsClient = None
    for client in ws_client_set:
        if client.websocket == websocket:
            odd_ws_client = client

    with open(file, "rb") as f:
        data = f.read()

    total_length = len(data)
    logger.debug(f"total_length={total_length}")

    while True:
        await asyncio.sleep(0.1)
        match odd_ws_client.state:
            case odd_asr_state.EM_ASR_STATE_IDLE:
                req = proto.TOddAsrApplyReq()
                req = {"name": "StartTranscription", "message_id": "", "token": "", "task_id": ""}

                str = proto.obj_to_dict_recursive(req)
                logger.debug(f">>>client doInit req: {str}")

                await websocket.send(json.dumps(req))
                logger.debug(f">>>client doInit req sent, timestamp_apply={odd_ws_client.timestamp_apply}")
                odd_ws_client.state = odd_asr_state.EM_ASR_STATE_APPLYING
                continue
            case odd_asr_state.EM_ASR_STATE_APPLYING:
                continue
            case odd_asr_state.EM_ASR_STATE_APLLY_OK:
                continue
            case odd_asr_state.EM_ASR_STATE_APPLY_FAILED:
                continue
            case odd_asr_state.EM_ASR_STATE_RECOGNIZING:

                chunk = data[offset:offset + chunk_size]
                await websocket.send(chunk)

                if odd_ws_client.timestamp_first_packet == 0:
                    odd_ws_client.timestamp_first_packet = time.time()
                    logger.debug(f"send chunk {offset}, odd_ws_client.timestamp_first_packet={odd_ws_client.timestamp_first_packet}")
                else:
                    logger.debug(f"send chunk {offset}")

                offset += chunk_size

                if offset >= total_length:
                    logger.info("send end")
                    break
                await asyncio.sleep(0.2)
                continue
            case _:
                continue

async def hello(server_url, file):
    client = OddWsClient(server_url)
    ws_client_set.add(client)

    async with connect(server_url) as websocket:
        client.websocket = websocket
        send_task = asyncio.create_task(send_messages(websocket, file))
        receive_task = asyncio.create_task(receive_messages(websocket))

        # 等待接收任务完成
        await asyncio.gather(send_task, receive_task)
        
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Your WAV file need to recognize to text.")
    parser.add_argument("audio_path", type=str, help="file path of your input WAV.")
    # Add server address parameter, allow it to be empty, set default value to None
    parser.add_argument("--server_url", type=str, default=None, help="Server WebSocket URL")
    # Add concurrent connection number parameter, allow it to be empty, set default value to None
    parser.add_argument("--concurrency", type=int, default=None, help="Number of concurrent connections")
    args = parser.parse_args()

    file = args.audio_path
    default_server_url = "ws://"+ config.WS_HOST +":"+ str(config.WS_PORT) +"/v1/asr"
    
    server_url = args.server_url if args.server_url is not None else default_server_url
    concurrency = args.concurrency if args.concurrency is not None else 1

    print(f"Current working directory: {os.getcwd()}")
    print(f"Full file path: {os.path.abspath(file)}")
    print(f"ASR server url: {server_url}, concurrency={concurrency}")
    

    if not os.path.exists(file):
        print(f"File not found: {file}")
        exit(1) 

    # detect current test file is wav file
    if not file.endswith(".wav") and not file.endswith(".pcm"):
        print(f"File format error: {file}. Please input wav or pcm file.")
        exit(1)

    # check file format, sample rate must be 16000, sample width must be 16bit, channels must be 1
    if file.endswith(".wav"):
        import soundfile as sf
        with sf.SoundFile(file) as f:
            if f.samplerate != 16000:
                print(f"File sample rate error: {file}. Please input 16000 sample rate, while input {f.samplerate}")
                exit(1)
            if f.subtype != 'PCM_16':
                print(f"File sample width error: {file}. Please input 16bit sample width, while input {f.subtype}")
                exit(1)
            if f.channels != 1:
                print(f"File channels error: {file}. Please input 1 channel, while input {f.channels}")
                exit(1)

    async def run_concurrent_tests():
        tasks = [hello(server_url, file) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

    asyncio.run(run_concurrent_tests())
