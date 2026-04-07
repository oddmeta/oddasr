**Read this in other languages: [English](README.en.md), [中文](README.md).**

# OddASR: A Simple ASR API Server for FunASR

![GitHub](https://img.shields.io/github/license/oddmeta/oddasr)

A simplest ASR API server for FunASR based on Flask, supporting both audio file mode and streaming mode transcriptions.

<font color=red>This document is the user guide for OddASR. If you are a developer and want to modify OddASR yourself, please refer to the developer documentation.</font>
- [Chinese Developer Guide](docs/README.chs.md)
- [English Developer Guide](docs/README.md)

## I. Preface

### 1. About OddASR

Since my project **[XiaoLuo TongXue](https://x.oddmeta.net)** needs ASR functionality, I encapsulated **[FunASR](https://github.com/modelscope/FunASR)** to enable voice conversation support for XiaoLuo TongXue.

Additionally, **[OddAgent](https://github.com/oddmeta/oddagent)** also uses OddASR to allow users to directly input voice on the web. If you're interested, you can also refer to the code in OddAgent.

Considering the wide use of ASR functionality, some friends have privately asked me about related usage and encapsulation issues, especially regarding streaming ASR support (there are many FunASR API encapsulations on GitHub, but all are offline file transcription, none support both offline file transcription and streaming transcription). I thought I might as well open-source it directly. I hope it helps students who need ASR functionality.

I've also done some evaluations on FunASR, FireRedAsr, Vosk, and other ASR projects, but overall, in my own usage scenarios, FunASR performs the best (no intention to belittle other ASRs, just limited to my own usage experience).

### 2. Why Should You Choose OddASR?

- **Simplified Deployment**: Easy-to-use REST API for ASR transcription.
- **Local Reference**: Standalone Python implementation for local ASR transcription.
- **Docker Support**: Dockerfiles supporting both GPU and CPU deployment.
- **Easy to Use**: Simple API requests for audio file transcription.

## II. Quick Start

### 1. Recommended Hardware

- CPU: 4 cores or more recommended.
- Storage: OddAsr Docker image (`oddasr-cpu:v0.1.0`) is approximately 2.4GB, ASR models require about 6GB, and logs need 500M space.
- Memory: 8GB or more recommended.

> My XiaoLuo TongXue uses a 99 RMB/year ECS from Alibaba Cloud with only 2 cores and 2GB RAM, which can't run the paraformer model. But I don't want to spend money on commercial APIs like XunFei/Alibaba/Baidu, so I used Vosk before.

### 2. Install OddASR

It is recommended to install in a virtual environment to avoid conflicts with other products and projects. I personally use conda, but you can also use venv, uv, poetry, etc. Here's the installation process using conda as an example.

Environment requirements: Python 3.10+

- 1. Create a test virtual environment

```bash
conda create -n oddasr python==3.10
conda activate oddasr
```

- 2. Install OddAgent in the virtual environment

```bash
pip install -i https://pypi.org/simple/ oddasr
```

> Non-official mirror sites may not have the latest version, so it's recommended to use the official PyPI source.

## III. Start OddASR

### 1. Start with Default Configuration

Simply execute the following command in the installed virtual environment to start:

```python
oddasr
```

It will start with the default configuration of oddasr, enabling both **file mode and streaming mode**, and each ASR supports one concurrent session.

### 2. Start with Custom Configuration

If you want to modify some parameters of oddasr for custom startup, you can first download a default configuration from here:

https://github.com/oddmeta/oddasr/blob/master/config.json.sample

Download it and rename it to `config.json`, then make some modifications to the configuration you need (see the following introduction for the configuration items supported by OddASR), and then start OddASR in the following way:

```python
oddasr -c config.json
```

### 3. Docker Start

OddASR also supports Docker startup, but I haven't packaged the image to Docker Hub. If you need Docker startup, I provide a Docker composer configuration, and you can package the image yourself.
- `Dockerfile`: CPU version
- `Dockerfile_GPU`: GPU version

For specific packaging and Docker running methods, please refer to the development documentation:
https://github.com/oddmeta/oddasr/blob/master/docs/README.chs.md

### 4. Notes

#### 1) Initial Startup Takes Time

<font color=red>**When running oddasr for the first time, it will download multiple model files from the internet, which takes quite some time, from 10 minutes to more, depending on your internet bandwidth. You also need to reserve at least 8G of storage space for these model files.**</font>

In addition, even if it's not the first run, the oddasr server still <font color=red>**needs a few minutes to start**</font> because by default, OddASR starts in preload mode to speed up response to ASR transcription requests.

Only when you see logs like the following does it mean OddASR has been initialized successfully and started:

```bash
2025-07-25T08:22:08.093187031Z  * Running on all addresses (0.0.0.0)
2025-07-25T08:22:08.093201526Z  * Running on http://127.0.0.1:9002
2025-07-25T08:22:08.093213810Z  * Running on http://172.17.0.2:8101
2025-07-25T08:22:08.093226351Z Press CTRL+C to quit
```

#### 2) Large Hard Disk Storage Requirements

OddASR integrates multiple different types of models, including ASR models/VAD detection models/punctuation models/speaker separation models. These models occupy relatively large hard disk space (and need to be downloaded during the first run), so if your hard disk space is tight, you can consider specifying the storage location after model download like me:

- Windows environment

```bash
set HF_ENDPOINT=https://hf-mirror.com
set HF_HOME=F:/ai_share/models
```

- Mac/Linux environment

```bash
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/data/ai_share/models
```

#### 3) Temporary File Permissions Issue

The background needs some temporary storage during transcription, and by default, temporary files are saved to the `/tmp` directory. Therefore, before running `oddasr`, be sure to confirm that you have read and write permissions for the `/tmp` directory, <font color=red>**otherwise errors like the following will occur**</font>:

```python
(index):742 XHR status: 500 Response text: {"error":"ASR processing error: ASR sentence generate error: Failed to load audio file: local variable 'parent' referenced before assignment"}
```

## IV. How to Use OddASR?

### 1. File ASR Transcription API

Simply put your file path in a form and send it to OddASR via HTTP POST.

```python
def test_file(audio_path: str, output_format: str = "txt"):
    # Set the service URL
    url = "http://127.0.0.1:9002/v1/asr"
    # Define hotwords
    hotwords = "XiaoLuo XiaoLuoTongXue OddMeta XiaoAo"
    # Open the audio file
    with open(audio_path, "rb") as audio_file:
        # Send POST request
        response = requests.post(url, files={"audio": audio_file}, data={"hotwords": hotwords, "mode": "file", "output_format": output_format})
        # Output results
        if response.status_code == 200:
            try:
                print("Recognition Result:", response.json()["text"])
            except ValueError:
                print("Non-JSON response:", response.text)  # Print the raw response
        else:
            print("Error:", response.text)  # Print the raw error message
```

For specific examples, please refer to: https://github.com/oddmeta/oddasr/blob/master/testAPI.py

The output format after transcription supports three formats:
- txt: Text mode
- spk: Speaker mode
- srt: Subtitle mode

Specific formats are shown below with examples.

### 2. Streaming ASR Transcription API

Streaming ASR transcription provides API interfaces via websocket. The entire API call flow is as follows:

'''    
    client --> server: connect
    client --> server: TCmdApppyAsrReq, msg_type = StartTranscription;
    server --> client: TCmdApplyAsrRes, msg_type = MSG_SUBSCRIBE_INIT_RES;
    client --> server: TCMDTranscribeReq, msg_type = MSG_TRANSCRIBE_REQ;
    server --> client: TCMDTranscribeRes, msg_type = MSG_TRANSCRIBE_RES;

    TCMDTranscribeReq
'''

For specific examples, please refer to: https://github.com/oddmeta/oddasr/blob/master/testStreamAPI.py

### 3. Sentence ASR Transcription API

Same as the file ASR transcription API, but the output format only supports text mode, not speaker mode or subtitle mode.

### 4. Test Script Examples

- Test scripts
    - **`testAPI.py`**: Example client script for testing the file mode of ASR API.
    - **`testStreamAPI.py`**: Example client script for testing the streaming mode of ASR API.
- Audio files
    - **`test_cn_male9s.wav`**: Example audio file for testing.
    - **`test_en_steve_jobs_10s.wav`**: Example audio file for testing.
    - **`test_cn_16k-16bits-mono.wav`**: Example audio file for streaming ASR testing.


#### 1) Test File ASR Transcription API

Use the `testAPI.py` script to test the API:

```bash
python testAPI.py test_en_steve_jobs_10s.wav txt
```

Example `curl` command:

- Send an audio file to the REST API

```bash
curl -X POST -F "audio=@path/to/audio.wav" http://127.0.0.1:12340/v1/asr
```

Example `curl` command for testing the `test_cn_male_9s.wav` audio file:

```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:12340/v1/asr
```

There are two test audio files in the repository:

- `test_cn_male9s.wav`
- `test_en_steve_jobs_10s.wav`

You can test them as follows:
```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:12340/v1/asr
curl -X POST -F "audio=@test_en_steve_jobs_10s.wav" http://127.0.0.1:12340/v1/asr
```

#### 2) Test Streaming ASR Transcription API

Use the `testStreamAPI.py` script to test the API, which supports pcm and wav files as test inputs.

- **Limitations**

<font color=red>OddAsr streaming mode currently only supports <b>16K sample rate, 16 bit width, mono</b> audio as input.</font>

You need to ensure your input audio format before feeding it to OddAsr, otherwise the transcription result may not meet your expectations. You can refer to testStreamAPI.py as a demonstration for implementing your own application.

- Input a pcm file as test input

```bash
python testStreamAPI.py 111.pcm
```

- Input a wav file as test input

```bash
python testStreamAPI.py test_cn_16k-16bits-mono.wav
```

If your test input is a wav file, `testStreamAPI.py` will check the sample rate and channel number, and will raise an error if they don't match.

```bash
python testStreamAPI.py test_cn_16k-16bits-mono.wav --concurrency 4
```

Simulate 4 real-time streaming requests to the server.


### 5. Example Output

#### 1) Text Mode

```bash
This is the start of this real-time transcription.
Yes, then this is the transcription effect, roughly like this.
Then you can also add a person to it here.
For example, I'll give it a random name,
Is it connected to the cloud or calculated locally? Connected to the cloud.
```

#### 2) Speaker Mode

```bash
Speaker 0: This is the start of this real-time transcription.
Speaker 0: Yes,
Speaker 0: then this is the transcription effect,
Speaker 0: roughly like this.
Speaker 0: Then you can also add a person to it here.
Speaker 0: For example, I'll give it a random name,
Speaker 1: Is it connected to the cloud or calculated locally? Connected to the cloud.
Speaker 0: Local, local, local. Yes,
Speaker 0: No need to connect, can it be adjusted?
Speaker 2: This also works,
Speaker 0: Then you can add a grid to it here.
```

#### 3) SRT Mode

```bash
0 00:00:01,010 --> 00:00:04,865 Speaker 0: This is the start of this real-time transcription.
1 00:00:06,040 --> 00:00:06,280 Speaker 0: Yes,
2 00:00:06,640 --> 00:00:08,660 Speaker 0: then this is the transcription effect,
3 00:00:08,680 --> 00:00:10,280 Speaker 0: roughly like this.
4 00:00:10,280 --> 00:00:14,500 Speaker 0: Then you can also add a person to it here.
5 00:00:14,660 --> 00:00:19,665 Speaker 0: For example, I'll give it a random name,
6 00:00:20,440 --> 00:00:23,200 Speaker 1: Is it connected to the cloud or calculated locally? Connected to the cloud.
7 00:00:23,240 --> 00:00:25,340 Speaker 0: Local, local, local. Yes,
8 00:00:25,340 --> 00:00:27,275 Speaker 0: No need to connect, can it be adjusted?
9 00:00:29,120 --> 00:00:31,480 Speaker 2: This also works,
10 00:00:32,130 --> 00:00:33,885 Speaker 0: Then you can add a grid to it here.
```

## V. Customize Your Own OddASR Configuration

Regarding the custom configuration function of OddASR, my initial idea was to add parameters in the command line so that users could customize the startup directly through command line parameters. However, there are too many parameters I need to support, so I gave up the command line parameter approach and directly used a configuration file instead.

Therefore, the current version of OddASR has removed the command line parameter custom configuration function and switched to using configuration files.

### 1. Default Configuration

By default, oddasr uses the address 0.0.0.0 and binds an HTTP port 9002 and a websocket port 8101.

Main configuration items are as follows:

- `HOST`: HTTP port configuration, default port number 9002. Used for file ASR transcription, as well as some demos and management functions.
- `WS_PORT`: Websocket port configuration, default port number 8101. Used for streaming ASR transcription.
- `preload_model`: Whether to preload models at startup, default True, so that it can respond quickly after receiving ASR transcription requests. Loading models is slow, from seconds to tens of seconds, depending on your CPU, memory hardware configuration, and the number of loaded instances.
- `enable_gpu`: Whether to enable GPU, default False, not using GPU.
- `disable_stream`: Streaming ASR transcription is enabled by default, default False.
- `concurrent_thread`: Number of concurrent threads, default 0, i.e., default to start threads with CPU cores.
- `max_instance`: Maximum number of instances, default 1, i.e., only supporting one concurrent transcription. If your hardware configuration is sufficient, you can set the maximum number of instances to a larger value to allow your OddASR to support more concurrent requests.

### 2. Complete Configuration Items

Specifically as follows:

```python
DEFAULT_CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 9002,                          # HTTP port
    "WS_HOST": "0.0.0.0",
    "WS_PORT": 8101,                       # Websocket port
    "Debug": False,
    "odd_asr_cfg": {
        "preload_model": True,             # Preload models at startup to
        "enable_gpu": False,               # Default not to use GPU
        "disable_stream": False,           # Default to enable streaming ASR transcription
        "concurrent_thread": 0,            # Default to start threads with CPU cores
        "asr_stream_cfg": {
            'max_instance': 1,              # Maximum number of streaming ASR transcription instances
            'save_audio': False,
            'punct_mini_len': 10,
            'punct_time_mini_force_trigger': 3,
            'free_resource_timeout': 5,
            'force_final_result': 20,
            'vad_threshold': 0.8,
            'vad_min_speech_duration': 300,
            'vad_min_silence_duration': 200
        },
        "asr_file_cfg": {
            'max_instance': 1,              # Maximum number of file ASR transcription instances
            'save_audio': False,
            'punct_mini_len': 10,
            'punct_time_mini_force_trigger': 3,
            'free_resource_timeout': 5,
            'force_final_result': 20,
            'vad_threshold': 0.8,
            'vad_min_speech_duration': 300,
            'vad_min_silence_duration': 200
        },
        "asr_sentence_cfg": {
            'max_instance': 1,              # Maximum number of sentence ASR transcription instances
            'save_audio': False,
            'punct_mini_len': 10,
            'punct_time_mini_force_trigger': 3,
            'free_resource_timeout': 5,
            'force_final_result': 20,
            'vad_threshold': 0.8,
            'vad_min_speech_duration': 300,
            'vad_min_silence_duration': 200
        },
        "enable_https": False,
        "ssl_cert_path": "scripts/cert.pem",
        "ssl_key_path": "scripts/key.pem",
    },
    "odd_asr_slp_cfg": {
        "sensitive_words": {
            "path": "scripts/sensitivewords",   # Path to sensitive words
        },
        "hotwords": {
            "path": "scripts/hotwords",        # Path to hotwords
        }
    },
    "db_cfg": {
        "db_engine": "sqlite",
        "db_name": "oddasr.db",
        "db_user": "",
        "db_password": "",
        "db_host": "",
        "db_port": "",
    },
    "redis_cfg": {
        "redis_enabled": False,
        "redis_host": "127.0.0.1",
        "redis_port": 7379,
        "redis_password": "",
    },
    "log_file": "oddasr.log",
    "log_path": "logs/",
    "log_level": 10,
    "asr": {'liveasr':'', 'appid':'oddasrtest', 'secret':'oddasrtest'},
    "Users": 'oddasr_users.json'
}
```

---

## VII. TODO List

- [ ] Add more models and features. Especially since I saw the FunASR-nano version model come out a few days ago, I've been wanting to try the effect, but I haven't had time.
- [ ] Add more custom options.
   - [ ] --output_format: txt means plain text, spk means adding speaker before each paragraph after VAD segmentation, srt means adding the time position of each paragraph in the audio file on top of spk
   - [ ] --hotword Hotword file, one hotword per line, format (hotword weight): Alibaba 20
- [ ] Add a simple UI demo for oddasr.
- [ ] Support voiceprint recognition!!! [XiaoLuo TongXue](https://x.oddmeta.net) really needs this feature!!!
- [ ] Other enhanced features
   - [ ] --thread_num Set the number of concurrent sending threads, default 1
   - [ ] --audio_in Audio files to be transcribed, supporting server local/remote file paths, file list wav.scp
   - [ ] --ssl Set whether to enable SSL certificate verification, default 1 enabled, set to 0 disabled
   - [ ] --use_itn Set whether to use itn, default 1 enabled, set to 0 disabled

---

## VIII. License

The OddASR project does not have any license.
Copy freely, without any strings attached! Just happy coding!