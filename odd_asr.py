# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr.py 
@info: 消息模版
"""

import torch
import librosa
import torchaudio

import os
from funasr import AutoModel
from utils_speech import convert_pcm_to_float, convert_time_to_millis, text_to_srt
from log import logger
import odd_asr_config as config
import threading

class OddAsrParamsFile:
    def __init__(self, mode="file", hotwords="", return_raw_text=True, is_final=True, sentence_timestamp=False):
        self._mode = mode  # mode should be a string like 'file','stream', 'pipeline'
        self._hotwords = hotwords  # hotwords should be a string like 'word1 word2'
        self._return_raw_text=return_raw_text #return raw text or not, default is True, if False, return json format result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]]}, 
        self._is_final=is_final  #is_final=True, if False, return partial result, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False},
        self._sentence_timestamp=sentence_timestamp  #sentence_timestamp=False, if True, return sentence timestamp, like: {text: "hello world", timestamp: [[0, 1000], [1000, 2000]], is_final: False, sentence_timestamp: [[0, 2000]]},
        self._is_busy=False

class OddAsrFile:
    """
    语音识别类，用于语音识别文件
    """
    _fileParam: OddAsrParamsFile = None
    _model: AutoModel = None
    _device = None

    def __init__(self, fileParam:OddAsrParamsFile=None):

        if fileParam is None:
            self._fileParam = OddAsrParamsFile()
        else:
            self._fileParam = fileParam

        if config.enable_gpu:
            # auto detect GPU _device
            if torch.cuda.is_available():
                self._device = "cuda:0"
            # elif torch.npu.is_available():
            #     self._device = "npu:0"
            else:
                self._device = "cpu"
        else:
            self._device = "cpu"

        # load model on init due to the model is large, and the model is not loaded on the first call
        self.load_file_model(self._device)

        self.lock = threading.Lock()  # mutex lock for _is_busy

    def load_file_model(self, device="cuda:0"):
        # load file model

        logger.info(f"Loading model with device={device}")

        self._model = AutoModel(
            # model="iic/speech_paraformer_asr_nat-zh-cn-16k-aishell2-vocab5212-pytorch",
            model="iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            vad_model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', vad_model_revision="v2.0.4",
            # punc_model='ct-punc',
            punc_model='iic/punc_ct-transformer_cn-en-common-vocab471067-large', punc_model_revision="v2.0.4",
            spk_model="cam++",
            # spk_model="iic/speech_campplus_sv_zh-cn_3dspeaker_16k",
            log_level="error",
            hub="ms",  # hub：表示模型仓库，ms为选择modelscope下载，hf为选择huggingface下载。
            device=device,
            disable_update=True
        )
        logger.info("Model loaded successfully.")

    def transcribe_file(self, audio_file, hotwords="", output_format="txt"):
        self.set_busy(True)
        try:
            # check audio file exists
            if not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                self.set_busy(False)
                raise FileNotFoundError(f"Audio file not found: {audio_file}")

            # load audio file
            logger.info(f"Loading audio file: {audio_file}")
            data, sr = librosa.load(audio_file, sr=None, mono=True)
            logger.info(f"Audio loaded successfully. Sample rate: {sr}")
            data = convert_pcm_to_float(data)

            # resample audio to 16kHz if necessary
            if sr != 16000:
                logger.info(f"Resampling audio from {sr} to 16000 Hz")
                data = torch.tensor(data, dtype=torch.float32).unsqueeze(0) # Add batch dimension
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
                data = resampler(data).squeeze(0).numpy()  # Resample and convert to numpy array
                logger.info(f"Audio resampled to 16000 Hz. Shape: {data.shape}")

            logger.info(f"Starting speech recognition with expected output_format={output_format}, hotwords: {hotwords}")

            if self._model is None:
                self.load_file_model(self._device)

            # start speech recognition with hotwords
            result = self._model.generate(
                data, 
                return_raw_text=True, 
                is_final=True, 
                sentence_timestamp=False,
                hotword=hotwords  # Pass the hotwords as a string to the _model
            )

            output_text = ""

            match output_format:
                case "srt":
                    sentences = result[0]["sentence_info"]
                    subtitles = []

                    logger.debug(f"sentence_info: {sentences}")

                    for idx, sentence in enumerate(sentences):
                        sub = text_to_srt(idx=idx, speaker_id=sentence['spk'], msg=sentence['text'], start_microseconds=sentence['start'], end_microseconds=sentence['end'])
                        subtitles.append(sub)

                    output_text = "\n".join(subtitles)
                case "spk":
                    sentences = result[0]["sentence_info"]
                    subtitles = []

                    for idx, sentence in enumerate(sentences):
                        sub = f"发言人 {sentence['spk']}: {sentence['text']}"
                        subtitles.append(sub)

                    output_text = "\n".join(subtitles)
                case "txt":
                    output_text = result[0]["text"]
                case _:
                    output_text = result[0]["text"]
            self.set_busy(False)
            return output_text

        except Exception as e:
            self.set_busy(False)
            raise RuntimeError(f"Error processing audio file: {e}")

    def set_busy(self, is_busy):
        with self.lock:  # 使用锁保护共享资源
            self._fileParam._is_busy = is_busy
            if not is_busy:
                logger.info(f"set_busy to False, done")

    def is_busy(self):
        with self.lock:  # 使用锁保护共享资源
            return self._fileParam._is_busy
