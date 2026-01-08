# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr_stream.py 
@info: 消息模版
"""

import torch
import numpy as np
import queue
import threading
import time
import re
import copy
import os
from funasr import AutoModel

from oddasr.log import logger
from oddasr.logic.odd_asr_result import enque_asr_result, OddAsrStreamResult
import oddasr.odd_asr_config as config

class AudioFrame:
    def __init__(self, data, sr: int = 16000, channel=1, bit_depth=16, timestamp = 0):
        self.data = copy.deepcopy(data)             # 音频数据
        self.frame_timestamp = timestamp            # 从启动转写线程时间开始计时的时间戳
        self.sr = sr                                # 采样率
        self.channel = channel                      # 声道数
        self.bit_depth = bit_depth                  # 位深度
    def reset(self):
        self.data = np.array([], dtype=np.float64)
        self.frame_timestamp = 0
        self.sr = 16000
        self.channel = 1
        self.bit_depth = 16

class OddAsrStats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.index = 0
        self.start_time = 0                         # 启动转写线程时间
        self.end_time = 0                           # 转写结束时间
        self.total_audio_recv_len = 0               # 接收音频总长度
        self.total_audio_input_len = 0              # 输入音频总长度
        self.total_asr_len = 0                      # 转写总长度
        self.total_asr_time = 0                     # 转写总时间
        self.last_recv_timestamp: float = 0.0       # 最后一次接收音频的时间戳
        self.last_reply_par_timestamp: float = 0.0  # 最后一次回复中间结果的时间戳
        self.last_reply_fin_timestamp: float = 0.0  # 最后一次生成最终结果的时间戳


class OddAsrParamsStream:
    _mode: str = "stream"
    _hotwords: str = "oddmeta xiaoluo"
    _rec_file:str =""
    _result_callback = None
    _result_callback: bool = False
    _is_final : bool = False
    _sentence_timestamp: bool = False

    _chunk_size:list = [0, 10, 5]
    _encoder_chunk_look_back: int = 4
    _decoder_chunk_look_back: int = 1

    _transcription_thread: threading.Thread = None
    _audio_queue: queue.Queue = None
    _stop_event: threading.Event = None
    _audio_cache: np.ndarray = np.array([], dtype=np.float64) 
    _text_cache: str = ""

    _is_busy = False
    _websocket = None
    _stats = OddAsrStats()
    task_id = None

    def __init__(self, 
                 mode="stream", 
                 hotwords="", 
                 audio_rec_filename="",
                 result_callback=None,
                 return_raw_text=True, 
                 is_final=True, 
                 sentence_timestamp=False, 
                 chunk_size=[0, 10, 5], 
                 encoder_chunk_look_back=4, 
                 decoder_chunk_look_back=1,
                 ):
        self._mode = mode  # mode should be a string like 'file','stream', 'pipeline'
        self._hotwords = hotwords  # hotwords should be a string like 'word1 word2'
        self._rec_file = audio_rec_filename  # audio_rec_filename should be a string like 'audio.wav'
        self._result_callback = result_callback

        self._return_raw_text=return_raw_text #return raw text or not, default is True, if False, return json format result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]]}, 
        self._is_final=is_final  #is_final=True, if False, return partial result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False},
        self._sentence_timestamp=sentence_timestamp  #sentence_timestamp=False, if True, return sentence timestamp, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False, sentence_timestamp: [[0, 2000]]},

        self._chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
        self._chunk_size = chunk_size  #chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking

        self._encoder_chunk_look_back = encoder_chunk_look_back #number of chunks to lookback for encoder self-attention
        self._decoder_chunk_look_back = decoder_chunk_look_back #number of encoder chunks to lookback for decoder cross-attention

        self._audio_queue = queue.Queue()
        self._stop_event = threading.Event()

        # free resource timeout, auto free resource if N seconds without receiving audio
        self._free_resource_timeout = config.odd_asr_cfg["asr_stream_cfg"]["free_resource_timeout"]
        if self._free_resource_timeout < 0:
            self._free_resource_timeout = 5

        # force to generate final result after N seconds
        self._force_final_result = config.odd_asr_cfg["asr_stream_cfg"]["force_final_result"]
        if self._force_final_result < 0:
            self._force_final_result = 20

        # force trigger punctuate if time elapses less than the configuration value
        self.punct_time_mini_force_trigger = config.odd_asr_cfg["asr_stream_cfg"]["punct_time_mini_force_trigger"]
        if self.punct_time_mini_force_trigger < 0:
            self.punct_time_mini_force_trigger = 3

        # minimum length of punctuation to trigger punctuate
        self.punct_mini_len = config.odd_asr_cfg["asr_stream_cfg"]["punct_mini_len"]
        if self.punct_mini_len < 0:
            self.punct_mini_len = 10

        # check chunk_size is valid, chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking, chunk_size[1] is the chunk size, in ms, chunk_size[2] is the overlap size, in ms
        if len(self._chunk_size) != 3:
            raise ValueError("chunk_size should be a list of 3 elements, chunk_size[0] is the first chunk size, in ms, 0 means no chunking, -1 means adaptive chunking, chunk_size[1] is the chunk size, in ms, chunk_size[2] is the overlap size, in ms")
        if self._chunk_size[0] < -1 or self._chunk_size[0] > 60000:
            raise ValueError("chunk_size[0] should be between -1 and 60000, in ms")
        if self._chunk_size[1] < 0 or self._chunk_size[1] > 60000:
            raise ValueError("chunk_size[1] should be between 0 and 60000, in ms")
        if self._chunk_size[2] < 0 or self._chunk_size[2] > 60000:
            raise ValueError("chunk_size[2] should be between 0 and 60000, in ms")
        
    def _default_callback(self, result):

        print(result)

class OddAsrStream:
    vad_model = None
    stream_model = None
    punc_model = None
    streamParam: OddAsrParamsStream = None
    device: str = "cuda:0"
    lock: threading.Lock = None

    def __init__(self, streamParam:OddAsrParamsStream=None):
        # 初始化 OddAsrParamsStream 实例
        if streamParam is None:
            self.streamParam = OddAsrParamsStream()
        else:
            self.streamParam = streamParam

        self.vad_model = None
        self.stream_model = None
        self.punc_model = None

        # auto detect GPU device
        if config.odd_asr_cfg["enable_gpu"]:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = "cpu"

        if config.odd_asr_cfg["preload_model"]:
            self._load_stream_model(self.device)

        self.lock = threading.Lock()  # 初始化锁

    def set_busy(self, is_busy):
        with self.lock:  # 使用锁保护共享资源
            self.streamParam._is_busy = is_busy
            if not is_busy:
                logger.info(f"set_busy to False, clear _stop_event, websocket={self.streamParam._websocket}, task_id={self.streamParam.task_id}")
                self.streamParam._stop_event.set()
                self.streamParam._transcription_thread.join()
                self.streamParam._transcription_thread = None
                self.streamParam._audio_queue.empty()
                logger.info(f"set_busy to False, clear _stop_event,done")

    def is_busy(self):
        with self.lock:  # 使用锁保护共享资源
            return self.streamParam._is_busy
        
    def set_websocket(self, websocket):
        with self.lock:  # 使用锁保护共享资源
            self.streamParam._websocket = websocket
    
    def get_websocket(self):
        with self.lock:  # 使用锁保护共享资源
            return self.streamParam._websocket
        
    def set_session_id(self, task_id):
        with self.lock:  # 使用锁保护共享资源
            self.streamParam.task_id = task_id

    def get_session_id(self):
        with self.lock:  # 使用锁保护共享资源
            return self.streamParam.task_id

    def _load_stream_model(self, device="cuda:0"):
        # load stream model
        if not self.stream_model:
            self.stream_model = AutoModel(
                model="paraformer-zh-streaming", model_revision="v2.0.4",

                # vad_model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', vad_model_revision="v2.0.4",
                # vad_model="fsmn-vad", vad_model_revision="v2.0.4",

                # punc_model='iic/punc_ct-transformer_cn-en-common-vocab471067-large', punc_model_revision="v2.0.4",
                # punc_model='iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-large', punc_model_revision="v2.0.4",
                # punc_model='iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727', punc_model_revision="v2.0.4",

                # spk_model="cam++",
                log_level="debug",
                hub="ms",  # hub：表示模型仓库，ms为选择modelscope下载，hf为选择huggingface下载。
                device=device,
                disable_update=True,
            )

        if not self.punc_model:
            '''
            from modelscope.pipelines import pipeline
            from modelscope.utils.constant import Tasks

            inference_pipeline = pipeline(
                task=Tasks.punctuation,
                model='damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727'
            )

            inputs = "跨境河流是养育沿岸|人民的生命之源长期以来为帮助下游地区防灾减灾中方技术人员|在上游地区极为恶劣的自然条件下克服巨大困难甚至冒着生命危险|向印方提供汛期水文资料处理紧急事件中方重视印方在跨境河流问题上的关切|愿意进一步完善双方联合工作机制|凡是|中方能做的我们|都会去做而且会做得更好我请印度朋友们放心中国在上游的|任何开发利用都会经过科学|规划和论证兼顾上下游的利益"
            vads = inputs.split("|")
            rec_result_all="outputs:"
            param_dict = {"cache": []}
            for vad in vads:
                rec_result = inference_pipeline(text_in=vad, param_dict=param_dict)
                rec_result_all += rec_result['text']

            print(rec_result_all)            
            '''

            self.punc_model = AutoModel(
                # model='iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-large', punc_model_revision="v2.0.4",
                model="iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727", model_revision="v2.0.4",
                hub="ms",  # hub：表示模型仓库，ms为选择modelscope下载，hf为选择huggingface下载。
                device=device,
                disable_update=True,
            )


    def transcribe_stream(self, audio_frame, socket, task_id):
        '''
        transcribe audio stream, support real-time transcription, 
        and return partial result, like: 
            {
                text: "hello world", 
                timestamp: [[0, 1000], [1000, 2000]], 
                is_final: False, 
                sentence_timestamp: [[0, 2000]]
            },
        and return final result, like:
            {
                text: "hello world",
                timestamp: [[0, 1000], [1000, 2000]],
                is_final: True,
                sentence_timestamp: [[0, 2000]]
            }

        1. start a thread to transcribe audio stream
        2. add input audio_frame to queue
        3. empty queue, yield result and stop transcribe thread if got an EOF
        '''
        try:
            # 初始化num_chunks变量，确保在任何情况下都有定义
            num_chunks = 0
            
            if self.streamParam._audio_queue is None:
                logger.error(f"_audio_queue is None")
                return ""
            if self.streamParam._stop_event is None:
                logger.error(f"_stop_event is None")
                return ""
            if self.stream_model is None:
                self._load_stream_model()
            
            # Create and start the transcription thread
            if self.streamParam._transcription_thread is None or not self.streamParam._transcription_thread.is_alive():
                self.streamParam._stop_event.clear()  # 确保 _stop_event 未被设置
                # self.streamParam._transcription_thread = threading.Thread(target=self._transcribe_thread_wrapper, args=(self.streamParam,))
                self.streamParam._transcription_thread = threading.Thread(target=self._transcribe_thread_wrapper)
                self.streamParam._transcription_thread.daemon = True  # 设置为守护线程

                logger.info(f"start transcription_thread, websocket={socket}, task_id={task_id}")

                self.streamParam._transcription_thread.start()
                self.streamParam._stats.start_time = time.time()
            # else:
            #     logger.info(f"transcription_thread is running, websocket={socket}, task_id={task_id}")

            # DONT terminite the thread, just add an empty audio_frame to queue, let the previous frames to be processed
            if audio_frame is None:  # Receive EOF signal
                if self.streamParam._audio_cache.size > 0:
                    # 直接将numpy数组放入队列（无需转换为bytes）
                    cache_array = (self.streamParam._audio_cache * 32768).astype(np.int16)
                    frame = AudioFrame(data=cache_array)
                    self.streamParam._audio_queue.put(frame)
                    self.streamParam._audio_cache = np.array([], dtype=np.float64)  # 清空缓存
                # 放入EOF信号
                frame = AudioFrame(data=None)
                self.streamParam._audio_queue.put(frame)
            else:
                if type(audio_frame) is not bytes:
                    logger.error(f"audio_frame is not bytes, type={type(audio_frame)}")
                    return ""

                # Convert bytes to a NumPy array of int16
                pcm_array = np.frombuffer(audio_frame, dtype=np.int16)
                # Convert the array to float64 and normalize it
                new_audio_array = pcm_array.astype(np.float64) / 32768.0

                # Ensure new_audio_array is 1-dimensional
                if new_audio_array.ndim == 0:
                    new_audio_array = np.array([new_audio_array], dtype=np.float64)
                
                chunk_stride = self.streamParam._chunk_size[1] * 960 # 600ms

                # 合并缓存和新音频数组
                with self.lock:  # 使用锁保护共享资源访问
                    combined_data = np.concatenate([self.streamParam._audio_cache, new_audio_array])
                    data_len = len(combined_data)

                # logger.debug(f"transcribe_stream, chunk_stride={chunk_stride}, pcm_array_len={len(pcm_array)}, new_audio_array_len={len(new_audio_array)}, data_len={data_len}")

                # 按chunk_stride分割numpy数组
                if data_len >= chunk_stride:
                    with self.lock:  # 使用锁保护共享资源访问
                        num_chunks = data_len // chunk_stride
                        # 处理完整块
                        for i in range(num_chunks):
                            start = i * chunk_stride
                            end = start + chunk_stride
                            chunk_data = combined_data[start:end].copy()  # 创建数据副本
                            time_offset = time.time() - self.streamParam._stats.start_time

                            frame = AudioFrame(data=chunk_data, timestamp=time_offset)
                            self.streamParam._audio_queue.put(frame)
                        # 保存剩余数据到缓存中
                        self.streamParam._audio_cache = combined_data[num_chunks * chunk_stride:].copy()  # 创建数据副本
                else:
                    # 数据不足chunk_stride，存入缓存
                    with self.lock:  # 使用锁保护共享资源访问
                        self.streamParam._audio_cache = combined_data.copy()  # 创建数据副本

                self.streamParam._stats.total_audio_recv_len += len(audio_frame)
                self.streamParam._stats.last_recv_timestamp = time.time()

        except Exception as e:
            logger.error(f"Error in transcribe_stream: {e}")
            self.streamParam._stop_event.set()  # Stop the thread in case of an error
            if self.streamParam._transcription_thread is not None and self.streamParam._transcription_thread.is_alive():
                self.streamParam._transcription_thread.join()  # Wait for the thread to finish
                self.streamParam._transcription_thread = None
            raise RuntimeError(f"Error processing audio stream: {e}")

    def _retrieve_words_array(self, pkt_timestamp_start, pkt_timestamp_end, text_result):
        words = []

        if isinstance(text_result, list) and len(text_result) > 0 and isinstance(text_result[0], dict) and 'words' in text_result[0]:
            words_array = text_result[0]['words']
            for word_array in words_array:
                words.append({
                    'word': word_array['word'],
                    'begin_time': word_array['begin_time'],
                    'end_time': word_array['end_time'],
                })
        else:
            words.append({
                'word': text_result[0]['text'],
                'begin_time': pkt_timestamp_start,
                'end_time': pkt_timestamp_end,
            })

        return words

    def _save_audio_rec(self, filename, audio_data, sample_rate=16000):
        try:
            # 保存文件
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            # 确保 audio_data 是 NumPy 数组
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)

            # 若 audio_data 是浮点数类型，转换回 16 位有符号整数
            if audio_data.dtype == np.float64:
                audio_data = (audio_data * 32767).astype(np.int16)

            # 直接写入二进制文件
            with open(filename, 'ab') as binfile:
                audio_data.tofile(binfile)
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")

    def _generate_vad_data(self, pcm_chunk, sd_sentences = [], sr=16000):
        if not self.vad_model:  # 如果没有VAD模型，则不进行VAD处理
            return None
        vad_result = self.vad_model.vad(pcm_chunk)

        if not vad_result.is_speech:
            logger.debug(f"No speech detected, skipping...")

        logger.info(f"VAD result: {vad_result}")


    def _generate_stream_asr(self, pcm_chunk, is_final = False, cache=None, hotwords=""):
        if not self.stream_model:
            return None, cache
        
        text = None
        try:
            # logger.debug(f"_generate_stream_asr:is_final={is_final}, pcm_chunk={type(pcm_chunk)}, len={len(pcm_chunk)}, shape={pcm_chunk.shape}, dtype={pcm_chunk.dtype}")

            text = self.stream_model.generate(input=pcm_chunk, 
                                                cache=cache, 
                                                is_final=is_final, 
                                                # return_raw_text=True,
                                                sentence_timestamp=True,
                                                # use_punc=True,
                                                # punc_threshold=0.5,
                                                hotword=hotwords, 
                                                chunk_size=self.streamParam._chunk_size, 
                                                encoder_chunk_look_back=self.streamParam._encoder_chunk_look_back, 
                                                decoder_chunk_look_back=self.streamParam._decoder_chunk_look_back
                                                )
            
            logger.debug(f"_generate_stream_asr: text_result={text}")

        except Exception as e:
            logger.error(f"Error transcribing audio chunk: {e}")
            text = None
        
        return text, cache

    def _generate_punctuation_input(self, text):
        if self.punc_model is None:
            return text

        try:
            input_text = text

            '''
            [
                {
                    'key': 'rand_key_CwYyBZFyUoYmC', 
                    'text': '一二三四五六七八七六五四三二一一三四五三三。打老虎传前明月光 疑是地上霜', 
                    'punc_array': tensor([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3])
                }
            ]
            '''
            punc_result = self.punc_model.generate(input=input_text, punc_threshold=0.5)
            logger.info(f"punctuation: \n\tinput={input_text}\n\tpunc_result={punc_result}")
            punc_result_text = punc_result[0]['text']

            # find the specified punctuations in the punc_result
            punct_pattern = re.compile(r'[。？！]')
            matches = list(punct_pattern.finditer(punc_result_text))

            if matches:
                # locate the last punctuation
                last_match = matches[-1]
                split_pos = last_match.end()
                current_text = punc_result_text[:split_pos]
                remaining_text = punc_result_text[split_pos:]

                return current_text, remaining_text
            else:
                return None, punc_result_text

        except Exception as e:
            logger.error(f"Error in punctuation process: {e}")

    def _release(self):
        # self.set_busy(False)
        # self.set_session_id(None)
        # self.set_websocket(None)
        self.streamParam._stop_event.set()
        self.streamParam._audio_queue.put(None)
        # self.streamParam._audio_queue.join()
        # self.streamParam._audio_queue.task_done()
        self.streamParam._stats.reset()

    def _transcribe_thread_wrapper(self):
        import asyncio
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
        # encoder_chunk_look_back = 4 #number of chunks to lookback for encoder self-attention
        # decoder_chunk_look_back = 1 #number of encoder chunks to lookback for decoder cross-attention
        is_final = False
        cache = {}
        hotwords = ""
        websocket = None

        tasks = []  # 用于存储所有异步任务

        if self.streamParam._hotwords is not None and self.streamParam._hotwords != "":
            hotwords = self.streamParam._hotwords.split(" ")

        try:
            while not self.streamParam._stop_event.is_set():
                # STEP 1. read from queue, timeout 1 second
                try:
                    frame: AudioFrame = self.streamParam._audio_queue.get(timeout=1)
                    if frame is None:
                        continue
                    logger.debug(f"AudioFrame timestamp={frame.frame_timestamp}, queue length: {self.streamParam._audio_queue.qsize()},websocket={self.streamParam._websocket}")
                except queue.Empty:  # sleep 100ms if read timeout
                    time.sleep(0.1)
                    timediff = time.time() - self.streamParam._stats.last_recv_timestamp
                    # 5 seconds without receiving audio, stop the thread
                    if timediff > self.streamParam._free_resource_timeout:
                        logger.warn(f"No audio received for {self.streamParam._free_resource_timeout} seconds, stopping transcription thread.")
                        is_final = True
                        break
                    continue

                if frame.data is None:  # EOF received
                    logger.warn(f"Received EOF signal, stopping transcription thread.")
                    is_final = True
                    # break

                # STEP 2. save the pcm to a record file
                if config.odd_asr_cfg["asr_stream_cfg"]["save_audio"]:
                    if self.streamParam._rec_file == "":
                        self.streamParam._rec_file = "tmp/" + self.streamParam.task_id + ".pcm"
                    logger.debug(f"save audio frame to {self.streamParam._rec_file}, sr={frame.sr}, len={len(frame.data)}")
                    self._save_audio_rec(self.streamParam._rec_file, frame.data, frame.sr)

                speech = frame.data.copy()  # 创建数据副本
                websocket = self.streamParam._websocket

                # STEP 3. Spit the audio to chunks, each chunk should match the chunk_size initialized in streamParam 
                chunk_stride = self.streamParam._chunk_size[1] * 960 # 600ms
                total_chunk_num = int(len(speech)/chunk_stride)
                # logger.info(f"Processing frame, stride: {chunk_stride}, data={len(speech)}, total_chunk_num={total_chunk_num}, is_final={is_final}")

                # 在_transcribe_thread_wrapper方法中，添加对音频块的有效性检查
                for i in range(total_chunk_num):
                    start = i * chunk_stride
                    end = start + chunk_stride
                    audio_chunk = speech[start:end].copy()  # 创建数据副本
                    
                    # 添加防御性检查
                    if len(audio_chunk) == 0:
                        logger.warning(f"Empty audio chunk at index {i}, skipping...")
                        continue
                    
                    # 检查audio_chunk是否为有效的numpy数组
                    if not isinstance(audio_chunk, np.ndarray) or audio_chunk.ndim != 1:
                        logger.warning(f"Invalid audio chunk format at index {i}, shape: {audio_chunk.shape if isinstance(audio_chunk, np.ndarray) else type(audio_chunk)}")
                        continue
                
                    ## STEP 3.1 VAD
                    vad_result = self._generate_vad_data(audio_chunk)
                    if vad_result and not vad_result.is_speech:
                        logger.debug(f"No speech detected in chunk {i}, skipping...")
                        continue

                    # STEP 4. Transcribe the audio chunk

                    ## stats: total_audio_input_len
                    self.streamParam._stats.total_audio_input_len += len(audio_chunk)
                    ## stats: pkt_timestamp
                    pkt_timestamp_start = frame.frame_timestamp  + i * chunk_stride / frame.sr
                    pkt_timestamp_end = pkt_timestamp_start + chunk_stride / frame.sr / total_chunk_num * (i+1) - i * chunk_stride / frame.sr

                    text = None
                    words = []
                    text_result, cache = self._generate_stream_asr(audio_chunk, is_final, cache, hotwords)

                    if isinstance(text_result, list) and len(text_result) > 0 and isinstance(text_result[0], dict) and 'text' in text_result[0]:
                        text = text_result[0]['text'].strip()
                        if len(text) == 0:
                            text = None
                    else:
                        text = None

                    if text is None:
                        continue
                    elif text is not None and len(text) > 0:
                        words = self._retrieve_words_array(pkt_timestamp_start, pkt_timestamp_end, text_result)
                        self.streamParam._text_cache += text
                        self.streamParam._stats.last_reply_par_timestamp = time.time()
                        logger.info(f"text in cache: {self.streamParam._text_cache}, start time: {pkt_timestamp_start}, end time: {pkt_timestamp_end}")
                        result = OddAsrStreamResult(websocket, self.streamParam._text_cache, is_final=False, index=self.streamParam._stats.index, begin_time=pkt_timestamp_start, end_time=pkt_timestamp_end, is_last=is_final, words=words)
                        enque_asr_result(result)
                    else:
                        logger.warning(f"Unexpected text format at index {i}: {text}")
                        continue

                    # dont input punc model if current length is less than the configuration value
                    # force trigger punctuate if time elapses less than the configuration value
                    time_diff = time.time() - self.streamParam._stats.start_time
                    if time_diff < self.streamParam.punct_time_mini_force_trigger:
                        # if the length of the text is less than the configuration value, skip
                        if len(self.streamParam._text_cache) < self.streamParam.punct_mini_len:
                            continue

                    # STEP 5. Generate the punctuations
                    punct_text, remain_text = self._generate_punctuation_input(self.streamParam._text_cache)
                    if websocket is not None:
                        if punct_text and len(punct_text) > 1:
                            self.streamParam._stats.last_reply_fin_timestamp = time.time()
                            result1 = OddAsrStreamResult(websocket, punct_text, is_final=True, index=self.streamParam._stats.index, begin_time=pkt_timestamp_start, end_time=pkt_timestamp_end)
                            enque_asr_result(result1)

                        if remain_text and len(remain_text) > 0:
                            self.streamParam._stats.last_reply_par_timestamp = time.time()
                            result2 = OddAsrStreamResult(websocket, remain_text, is_final=False, index=self.streamParam._stats.index, begin_time=pkt_timestamp_start, end_time=pkt_timestamp_end)
                            enque_asr_result(result2)

                            # remove punctuations from the remaining text
                            self.streamParam._text_cache = re.sub(r'[。？！，；：“”‘’（）【】{}、,;:"\'()\[\]{}]', '', remain_text)

                            logger.info(f"current_text={remain_text}, after remove punctuations={self.streamParam._text_cache}")

                    else:
                        self.streamParam._text_cache = remain_text

                time.sleep(0.1)

            logger.info(f"Transcription thread stopped.")

            if websocket is not None:
                self.streamParam._stats.last_reply_par_timestamp = time.time()
                result = OddAsrStreamResult(websocket, "END", is_final=True, is_last=True, begin_time=pkt_timestamp_start, end_time=pkt_timestamp_end)
                enque_asr_result(result)

            if tasks:
                loop.run_until_complete(asyncio.gather(*tasks))

        except Exception as e:
            logger.error(f"Error in transcription thread: {e}")
        finally:
            logger.info(f"Transcription thread stopped.")
            loop.close()
            self._release()