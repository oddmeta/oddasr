**Read this in other languages: [English](README.md), [中文](README.chs.md).**

[TOC]

Here’s a draft for the `README.md` file based on your project:

---

# OddASR: A Simple ASR API Server for FunASR

![GitHub](https://img.shields.io/github/license/oddmeta/oddasr)

A simplest ASR API server for FunASR based on Flask, supporting both audio file mode and streaming mode transcriptions.

## Introduction

**[FunASR](https://github.com/modelscope/FunASR)** is a powerful open-source speech recognition (ASR) library developed by ModelScope.
It provides a wide range of pre-trained models and tools for various speech recognition tasks.
This repository aims to simplify the deployment of FunASR for non-realtime audio processing which is my another project ([小落同学](https://x.oddmeta.com)) needed.

## Why OddASR?

- **Simplified Deployment**: Easy-to-use REST API for ASR transcription.
- **Local Reference**: A standalone Python implementation for local ASR transcription.
- **Docker Support**: Dockerfiles for both GPU and CPU deployment.
- **Easy to Use**: Simple API requests for audio file transcription.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/oddmeta/oddasr.git
   cd oddasr
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Configurations for OddAsr server

You can configure the server by editting `odd_asr_config.py`, here are some important parameters:

- `PORT`: The port number for the file ASR server.
- `WS_PORT`: The port number for the stream ASR server.
- `concurrent_thread`: The number of concurrent threads for the server.
- `disable_stream`: Set to `True` to disable the stream ASR server.

more configurations can be found in `odd_asr_config.py`

### 2. Run the REST API Server

To start the REST API server:

```bash
python main_server.py
```

The OddASR server will start **both file mode and stream mode** in default configuration.

If the memory usage of your running environment is critical, you can disable stream mode by editting `odd_asr_config.py` and set `disable_stream = True`

The file ASR server will start on `http://127.0.0.1:9002`, and the stream ASR server will start on `http://127.0.0.1:8101`.

### 3. Recommended hardware

- CPU: 4 cores or more is recommended.
- Storage: OddAsr docker image(oddasr-cpu:v0.1.0) size is about 2.4GB, and you need about 6GB spaces for the ASR models, and 500M spaces for the logs.
- Memory: 8GB or more is recommended.

### 4. Test file ASR API

Use the `testAPI.py` script to test the API:
```bash
python testAPI.py test_en_steve_jobs_10s.wav txt
```

Example `curl` command:

- Send an audio file to the REST API

```bash
curl -X POST -F "audio=@path/to/audio.wav" http://127.0.0.1:9002/v1/asr
```

Example `curl` command for testing the `test_cn_male_9s.wav` audio file:

```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:9002/v1/asr
```

there are two test audio files in the repo:

- `test_cn_male9s.wav`
- `test_en_steve_jobs_10s.wav`

you can test them by:
```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:9002/v1/asr
curl -X POST -F "audio=@test_en_steve_jobs_10s.wav" http://127.0.0.1:9002/v1/asr
```

### 5. Test stream ASR API
Use the `testStreamAPI.py` script to test the API, supports pcm and wav file as test input.

- **Limitations**

<font color=red>OddAsr streaming mode current supports only <b>16K sample rate, 16 bit width, mono</b> audio as input.</font>

You need assure your input audio format before feeding them to OddAsr, otherwise the transcription result would not be the one you expected. You can refer to testStreamAPI.py as a demostration for the implementation of your own application.

- Input a pcm file as test input
```bash
python testStreamAPI.py 111.pcm
```

- Input a wav file as test input

```bash
python testStreamAPI.py test_cn_16k-16bits-mono.wav
```
If your test input is a wav file, `testStreamAPI.py` will check sample rate and channel number, if not match, will raise error.

```bash
python testStreamAPI.py test_cn_16k-16bits-mono.wav --concurrency 4
```
Simulate 4 real-time streaming requests to the server.


### 6. Example output

- text mode

```bash
是开始这个呃实时的一个转写。
对， 然后是转写的一个效果， 大概大概就是这个样子。 
然后的话那个在这里边你也可以去给他那个加一个人。 
比如说是嗯我随便给他取一个名字， 
就是连云端的还是自己算的连云端的吧。 
```

- spk mode

```bash
发言人 0: 是开始这个呃实时的一个转写。
发言人 0: 对，
发言人 0: 然后是转写的一个效果，
发言人 0: 大概大概就是这个样子。
发言人 0: 然后的话那个在这里边你也可以去给他那个加一个人。
发言人 0: 比如说是嗯我随便给他取一个名字，
发言人 1: 就是连云端的还是自己算的连云端的吧。
发言人 0: 呃本地的本地的本地的对，
发言人 0: 不用连看能调吧。
发言人 2: 这个还有对呀，
发言人 0: 然后这里边可以给他加格。
```

- srt mode

```bash
0 00:00:01,010 --> 00:00:04,865 发言人 0: 是开始这个呃实时的一个转写。 
1 00:00:06,040 --> 00:00:06,280 发言人 0: 对， 
2 00:00:06,640 --> 00:00:08,660 发言人 0: 然后是转写的一个效果， 
3 00:00:08,680 --> 00:00:10,280 发言人 0: 大概大概就是这个样子。 
4 00:00:10,280 --> 00:00:14,500 发言人 0: 然后的话那个在这里边你也可以去给他那个加一个人。 
5 00:00:14,660 --> 00:00:19,665 发言人 0: 比如说是嗯我随便给他取一个名字， 
6 00:00:20,440 --> 00:00:23,200 发言人 1: 就是连云端的还是自己算的连云端的吧。 
7 00:00:23,240 --> 00:00:25,340 发言人 0: 呃本地的本地的本地的对， 
8 00:00:25,340 --> 00:00:27,275 发言人 0: 不用连看能调吧。 
9 00:00:29,120 --> 00:00:31,480 发言人 2: 这个还有对呀， 
10 00:00:32,130 --> 00:00:33,885 发言人 0: 然后这里边可以给他加格。 
```

---

## Repository Contents

### 1. Core Files
- **`main_server.py`**: Implements the REST API server for ASR transcription.
- **`main_local.py`**: A standalone Python implementation for local ASR transcription.
- **`odd_asr_app.py`**: Main application file for running the REST API server.
- **`odd_asr_config.py`**: Custom configurations for the project.
- **`odd_asr_exception.py`**: Custom exception classes for the project.
- **`odd_asr_result.py`**: Result classes for the project.
- **`odd_asr.py`**: File ASR class for the project.
- **`odd_asr_stream.py`**: Stream ASR class for the project.
- **`odd_wss_server.py`**: Websocket server class for streaming ASR.
- **`utils_speech.py`**: Utility functions used by the REST API which was origined from FunASR repo.
- **`log.py`**: Logging configuration for the project.
- **`router/asr_api.py`**: Defines the API endpoints for the REST API.
- **`router/asr_front.py`**: Defines the front-end endpoints for the REST API.

### 2. Testing and Examples
- **`testAPI.py`**: Example client script to test the file mode of ASR API.
- **`testStreamAPI.py`**: Example client script to test the streaming mode of ASR API.

### 3. Audio Files
- **`test_cn_male9s.wav`**: Example audio file for testing.
- **`test_en_steve_jobs_10s.wav`**: Example audio file for testing.
- **`test_cn_16k-16bits-mono.wav`**: Example audio file for streaming ASR testing.

### 4. Deployment Files

- **`Dockerfile`**: Dockerfile for building GPU-accelerated Docker images (NVIDIA GPU deployment).
- **`Dockerfile_CPU`**: Dockerfile for building Docker images for simple CPU-based deployments.

### 5. Additional Files

- **`requirements.txt`**: Python dependencies required for the project.

---

## Features

### 1. REST API for ASR

- `main_server.py`Provides a REST API endpoint for audio file transcription.
- Built using Flask.
- Example usage: `python main_server.py`.

### 2. Docker Support

- Includes Dockerfiles for both GPU and CPU deployment.
- Simplifies deployment on servers with or without GPU support.

*BTW: I don't have a GPU to run test for GPU deployment, help wanted!*

---

## Docker Deployment

### 1. Install Docker

```bash
sudo apt-get update
sudo apt-get install -y docker.io
```

Visit https://docs.oddmeta.net/#/engine-api/install_docker_on_ubuntu or https://docs.docker.com/engine/install/ubuntu/ for more details.

### 2. CPU Deployment

```bash
docker build -t oddasr-cpu:v0.1.0 .
docker run -d -p 9002:9002 -p 8101:8101 --name oddasr-cpu oddasr-cpu:v0.1.0
```

### 3. GPU Deployment

```bash
docker build -f Dockerfile_GPU -t oddasr-gpu:v0.1.0 .
docker run -d -p 9002:9002 -p 8101:8101 --name oddasr-gpu oddasr-gpu:v0.1.0
```

### 4. About running oddasr container

In the first run of oddasr container, it will download the model files from the internet, this would take quite sometime, from 10 minutes to more, depends on the bandwith of your internet.
Even not for the first run, oddasr server still need a few minutes to startup, because we will load the model on startup to speed up the incoming ASR requests.

You can use `docker logs -t oddasr` to check the download progress. If you find logs like below, it means oddasr has already download the model files, running and working.

```
2025-07-25T08:22:08.090277794Z 2025-07-25 08:22:08 INFO odd_asr_result.py:95 (1-124264901494464) - => Start ASR result dispatch Task Success 
2025-07-25T08:22:08.093144025Z WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
2025-07-25T08:22:08.093187031Z  * Running on all addresses (0.0.0.0)
2025-07-25T08:22:08.093201526Z  * Running on http://127.0.0.1:9002
2025-07-25T08:22:08.093213810Z  * Running on http://172.17.0.2:9002
2025-07-25T08:22:08.093226351Z Press CTRL+C to quit
2025-07-25T08:22:08.372302454Z 2025-07-25 08:22:08,371 - modelscope - INFO - Use user-specified model revision: v2.0.4
2025-07-25T08:22:11.962184545Z 2025-07-25 08:22:11 DEBUG odd_asr_result.py:64 (1-124264901494464) - =============================================notifyTask: start=================================== 
```

### 5. Some docker commands for Docker newbies
- run oddasr container: `docker run -d -p 9002:12345 -p 8101:12346 --name oddasr-cpu oddasr-cpu:v0.1.0`
- list all running containers: `docker ps`
- print container logs: `docker logs -t oddasr-cpu`
- enter bash of your container: `docker exec -it oddasr-cpu bash`
- stop oddasr container: `docker stop oddasr-cpu`
- remove container: `docker rm oddasr-cpu`
- list container images: `docker images`
- remove image: `docker rmi IMAGE-ID`. `IMAGE-ID` is the image id, you can get it from `docker images`

---

## TODO

- [ ] Add more models and features.
- [ ] Support realtime ASR.
- [ ] Add more customized options.
   - [ ] --output_format: txt表示纯文本, spk表示根据VAD分段后每个段落前面加发言人，srt表示在spk基础上为每个段落加一个段落在音频文件中的时间位置
   - [ ] --hotword 热词文件，每行一个热词，格式(热词 权重)：阿里巴巴 20
- [ ] Simple UI for oddasr to demostrate.
- [ ] Support voiceprint recognition!!! [小落同学](https://x.oddmeta.net) really need this feature!!!
- [ ] Other enhancements
   - [ ] --thread_num 设置并发发送线程数，默认为1
   - [ ] --audio_in 需要进行转写的音频文件，支持服务器本地/远程文件路径，文件列表wav.scp
   - [ ] --ssl 设置是否开启ssl证书校验，默认1开启，设置为0关闭
   - [ ] --use_itn 设置是否使用itn，默认1开启，设置为0关闭

---

## Limitations

- ~~Only supports **non-realtime** ASR transcription.~~
- Only supports **audio files** as input.

---

## References

- [FunASR](https://github.com/modelscope/FunASR): The ASR framework used in this project.
- [Flask](https://github.com/pallets/flask): The web framework used for the REST API, which is based on Werkzeug and Jinja.
- [funasr-python-api](https://github.com/open-yuhaoz/funasr-python-api): Python api written by funasr server post

---

## License
This project is NOT licensed under any License.
Copy free, without any string attached! Just happy coding!
