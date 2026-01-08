**Read this in other languages: [English](README.en.md), [中文](README.md).**

# OddASR: 基于FunASR的简单ASR API服务器

![GitHub](https://img.shields.io/github/license/oddmeta/oddasr)

一个基于Flask的最简单的FunASR ASR API服务器，支持音频文件模式和流式模式转录。

## 介绍

**[FunASR](https://github.com/modelscope/FunASR)** 是ModelScope开发的一个强大的开源语音识别（ASR）库。
它提供了广泛的预训练模型和工具，用于各种语音识别任务。
这个仓库旨在简化FunASR的部署，用于非实时音频处理，这是我的另一个项目（[小落同学](https://x.oddmeta.com)）所需要的。

## 为什么选择OddASR？

- **简化部署**：易于使用的ASR转录REST API。
- **本地参考**：用于本地ASR转录的独立Python实现。
- **Docker支持**：同时支持GPU和CPU部署的Dockerfile。
- **易于使用**：用于音频文件转录的简单API请求。

## 安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/oddmeta/oddasr.git
   cd oddasr
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用

### 1. OddAsr服务器配置

你可以通过编辑`odd_asr_config.py`来配置服务器，以下是一些重要参数：

- `PORT`：文件ASR服务器的端口号。
- `WS_PORT`：流式ASR服务器的端口号。
- `concurrent_thread`：服务器的并发线程数。
- `disable_stream`：设置为`True`可禁用流式ASR服务器。

更多配置可在`odd_asr_config.py`中找到。

### 2. 运行REST API服务器

启动REST API服务器：

```bash
python main_server.py
```

在默认配置下，OddASR服务器将同时启动**文件模式和流式模式**。

如果您的运行环境内存使用紧张，可以通过编辑`odd_asr_config.py`并设置`disable_stream = True`来禁用流式模式。

文件ASR服务器将在`http://127.0.0.1:9002`上启动，流式ASR服务器将在`http://127.0.0.1:8101`上启动。

### 3. 推荐硬件

- CPU：建议4核或更多。
- 存储：OddAsr Docker镜像（oddasr-cpu:v0.1.0）大小约为2.4GB，ASR模型需要约6GB空间，日志需要500M空间。
- 内存：建议8GB或更多。

### 4. 测试文件ASR API

使用`testAPI.py`脚本测试API：
```bash
python testAPI.py test_en_steve_jobs_10s.wav txt
```

示例`curl`命令：

- 将音频文件发送到REST API

```bash
curl -X POST -F "audio=@path/to/audio.wav" http://127.0.0.1:9002/v1/asr
```

测试`test_cn_male_9s.wav`音频文件的示例`curl`命令：

```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:9002/v1/asr
```

仓库中有两个测试音频文件：

- `test_cn_male9s.wav`
- `test_en_steve_jobs_10s.wav`

您可以通过以下方式测试它们：
```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:9002/v1/asr
curl -X POST -F "audio=@test_en_steve_jobs_10s.wav" http://127.0.0.1:9002/v1/asr
```

### 5. 测试流式ASR API

使用`testStreamAPI.py`脚本测试API，支持pcm和wav文件作为测试输入。

- **限制**

<font color=red>OddAsr流式模式当前仅支持<b>16K采样率、16位宽、单声道</b>音频作为输入。</font>

在将音频输入OddAsr之前，您需要确保其格式正确，否则转录结果可能不符合预期。您可以参考testStreamAPI.py作为实现自己应用程序的演示。

- 输入pcm文件作为测试输入
```bash
python testStreamAPI.py 111.pcm
```

- 输入wav文件作为测试输入

```bash
python testStreamAPI.py test_cn_16k-16bits-mono.wav
```
如果您的测试输入是wav文件，`testStreamAPI.py`将检查采样率和通道数，如果不匹配，将引发错误。

```bash
python testStreamAPI.py test_cn_16k-16bits-mono.wav --concurrency 4
```
模拟4个实时流式请求到服务器。


### 6. 示例输出

- 文本模式

```bash
是开始这个呃实时的一个转写。
对， 然后是转写的一个效果， 大概大概就是这个样子。 
然后的话那个在这里边你也可以去给他那个加一个人。 
比如说是嗯我随便给他取一个名字， 
就是连云端的还是自己算的连云端的吧。 
```

- 发言人模式

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

- SRT模式

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

## 仓库内容

### 1. 核心文件
- **`main_server.py`**：实现ASR转录的REST API服务器。
- **`main_local.py`**：用于本地ASR转录的独立Python实现。
- **`odd_asr_app.py`**：运行REST API服务器的主应用文件。
- **`odd_asr_config.py`**：项目的自定义配置。
- **`odd_asr_exception.py`**：项目的自定义异常类。
- **`odd_asr_result.py`**：项目的结果类。
- **`odd_asr.py`**：项目的文件ASR类。
- **`odd_asr_stream.py`**：项目的流式ASR类。
- **`odd_wss_server.py`**：用于流式ASR的WebSocket服务器类。
- **`utils_speech.py`**：REST API使用的实用函数，源自FunASR仓库。
- **`log.py`**：项目的日志配置。
- **`router/asr_api.py`**：定义REST API的API端点。
- **`router/asr_front.py`**：定义REST API的前端端点。

### 2. 测试和示例
- **`testAPI.py`**：测试ASR API文件模式的示例客户端脚本。
- **`testStreamAPI.py`**：测试ASR API流式模式的示例客户端脚本。

### 3. 音频文件
- **`test_cn_male9s.wav`**：用于测试的示例音频文件。
- **`test_en_steve_jobs_10s.wav`**：用于测试的示例音频文件。
- **`test_cn_16k-16bits-mono.wav`**：用于流式ASR测试的示例音频文件。

### 4. 部署文件

- **`Dockerfile`**：用于构建GPU加速Docker镜像的Dockerfile（NVIDIA GPU部署）。
- **`Dockerfile_CPU`**：用于构建简单CPU部署Docker镜像的Dockerfile。

### 5. 其他文件

- **`requirements.txt`**：项目所需的Python依赖。

---

## 功能

### 1. ASR的REST API

- `main_server.py`提供了用于音频文件转录的REST API端点。
- 使用Flask构建。
- 示例用法：`python main_server.py`。

### 2. Docker支持

- 包括适用于GPU和CPU部署的Dockerfile。
- 简化了在有或没有GPU支持的服务器上的部署。

*顺便说一下：我没有GPU来运行GPU部署的测试，需要帮助！*

---

## Docker部署

### 1. 安装Docker

```bash
sudo apt-get update
sudo apt-get install -y docker.io
```

访问https://docs.oddmeta.net/#/engine-api/install_docker_on_ubuntu或https://docs.docker.com/engine/install/ubuntu/了解更多详情。

### 2. CPU部署

```bash
docker build -t oddasr-cpu:v0.1.0 .
docker run -d -p 9002:9002 -p 8101:8101 --name oddasr-cpu oddasr-cpu:v0.1.0
```

### 3. GPU部署

```bash
docker build -f Dockerfile_GPU -t oddasr-gpu:v0.1.0 .
docker run -d -p 9002:9002 -p 8101:8101 --name oddasr-gpu oddasr-gpu:v0.1.0
```

### 4. 关于运行oddasr容器

在首次运行oddasr容器时，它将从互联网下载模型文件，这需要相当长的时间，从10分钟到更长时间不等，具体取决于您的互联网带宽。
即使不是首次运行，oddasr服务器仍然需要几分钟才能启动，因为我们会在启动时加载模型以加快传入的ASR请求。

您可以使用`docker logs -t oddasr`来检查下载进度。如果您看到如下日志，则表示oddasr已经下载了模型文件，正在运行并正常工作。

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

### 5. 给Docker新手的一些docker命令
- 运行oddasr容器：`docker run -d -p 9002:12345 -p 8101:12346 --name oddasr-cpu oddasr-cpu:v0.1.0`
- 列出所有正在运行的容器：`docker ps`
- 打印容器日志：`docker logs -t oddasr-cpu`
- 进入容器的bash：`docker exec -it oddasr-cpu bash`
- 停止oddasr容器：`docker stop oddasr-cpu`
- 删除容器：`docker rm oddasr-cpu`
- 列出容器镜像：`docker images`
- 删除镜像：`docker rmi IMAGE-ID`。`IMAGE-ID`是镜像ID，您可以从`docker images`获取。

---

## 待办事项

- [ ] 添加更多模型和功能。
- [ ] 支持实时ASR。
- [ ] 添加更多自定义选项。
   - [ ] --output_format: txt表示纯文本, spk表示根据VAD分段后每个段落前面加发言人，srt表示在spk基础上为每个段落加一个段落在音频文件中的时间位置
   - [ ] --hotword 热词文件，每行一个热词，格式(热词 权重)：阿里巴巴 20
- [ ] 为oddasr添加简单UI演示。
- [ ] 支持声纹识别！！！[小落同学](https://x.oddmeta.net)真的需要这个功能！！！
- [ ] 其他增强功能
   - [ ] --thread_num 设置并发发送线程数，默认为1
   - [ ] --audio_in 需要进行转写的音频文件，支持服务器本地/远程文件路径，文件列表wav.scp
   - [ ] --ssl 设置是否开启ssl证书校验，默认1开启，设置为0关闭
   - [ ] --use_itn 设置是否使用itn，默认1开启，设置为0关闭

---

## 限制

- ~~仅支持**非实时**ASR转录。~~
- 仅支持**音频文件**作为输入。

---

## 参考

- [FunASR](https://github.com/modelscope/FunASR)：本项目中使用的ASR框架。
- [Flask](https://github.com/pallets/flask)：用于REST API的Web框架，基于Werkzeug和Jinja。
- [funasr-python-api](https://github.com/open-yuhaoz/funasr-python-api)：由funasr server post编写的Python API。

---

## 许可证

该项目没有任何许可证。
自由复制，没有任何附加条件！只需快乐编码！
        