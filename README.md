**Read this in other languages: [中文](README.md), [English](README.en.md).**

# OddASR: 基于FunASR的简单ASR API服务器

[TOC]

![GitHub](https://img.shields.io/github/license/oddmeta/oddasr)

一个基于Flask的最简单的FunASR ASR API服务器，支持音频文件模式和流式模式转录。

<font color=red>本文档是OddASR的使用文档, 如果你是一个开发者, 想自行对 OddASR 做一些修改, 请参考开发文档。</font>
- [中文开发文档](docs/README.chs.md)
- [English Developer Readme](docs/README.md)

## 一、前言

### 1. 关于OddASR

由于我在做的**[小落同学](https://x.oddmeta.net "小落同学")**项目需要用到ASR功能，所以我就将**[FunASR](https://github.com/modelscope/FunASR)**给封装了一下，让小落同学可以支持语音对话。

此外, **[OddAgent](https://github.com/oddmeta/oddagent "OddAgent")**项目里也用到了OddASR, 让用户可以在Web上直接用语音输入, 感兴趣的也可以参考一下 OddAgent 那边的代码。

而考虑到ASR功能的用途广泛，之前也有一些朋友私下问过我相关的一些使用和封装的问题，尤其是流式ASR的支持（github上有好多FunASR的API封装，但是全是离线文件转写的，没有一个同时支持离线文件转写和流式转写的API封装项目），想了一下干脆直接把它开源出来吧。希望对有ASR需求的同学有帮助。

之前针对 FunASR、FireRedAsr、Vosk等ASR项目也做了一些评测，但是总体跑下来发现在我自己的使用场景下还是FunASR的整体表现最好（没有任何要贬低其它一些ASR的意思，仅限于我自己的使用体验）。

### 2. 为什么建议你选择OddASR？

- **简化部署**：易于使用的ASR转录REST API。
- **本地参考**：用于本地ASR转录的独立Python实现。
- **Docker支持**：同时支持GPU和CPU部署的Dockerfile。
- **易于使用**：用于音频文件转录的简单API请求。

## 二、快速开始

### 1. 推荐硬件

- CPU：建议4核或更多。
- 存储：OddAsr Docker镜像（`oddasr-cpu:v0.1.0`）大小约为2.4GB，ASR模型需要约6GB空间，日志需要500M空间。
- 内存：建议8GB或更多。

> 我的小落同学用的是阿里云上99元每年的ECS, 只有2核2G，跑不动paraformer的模型，但是我又不想花钱去买讯飞/阿里/百度等的商业化的API，所以之前用的vosk．

### 2. 安装OddASR

建议在一个虚拟环境里安装，以避免与其它的产品和项目冲突。我个人习惯用conda，你用venv, uv，poetry什么也都OK。下面以conda为例介绍整个安装。

环境要求: Python 3.10+

- 1. 创建测试用的虚拟环境

```bash
conda create -n oddasr python==3.10
conda activate oddasr
```

- 2. 在虚拟环境里安装OddAgent

```bash
pip install -i https://pypi.org/simple/ oddasr
```

> 非官方的镜像站可能不一定能找到最新版本，因此建议使用pypi官方源。

## 三、启动 OddASR

### 1. 默认配置启动

直接在安装好的虚拟环境下，执行下面的命令即可启动

```python
oddasr
```

启动后将以oddasr默认的配置来运行，同时启动**文件模式和流式模式**，并且每一种ASR都支持一路并发。

### 2. 自定义配置启动

如果你希望修改 oddasr 的一些参数来自定义启动的话，可以先从这里下载一份默认配置

https://github.com/oddmeta/oddasr/blob/master/config.json.sample

下载下来后将其改名为`config.json`，然后对你需要的配置做一些修改（具体OddASR支持的配置项看后面的介绍），然后再以下面的方式来启动 OddASR

```python
oddasr -c config.json
```

### 3. Docker启动

OddASR也支持Docker启动，但是我没有打包image放到Docker Hub，若需要Docker启动，我提供了Docker composer配置，你可以自行打包image。
- `Dockerfile`：CPU版本
- `Dockerfile_GPU`：GPU版本

具体如何打包, 如何Docker运行可以参考一下开发文档: 
https://github.com/oddmeta/oddasr/blob/master/docs/README.chs.md

### 4. 注意事项

#### 1) 初始化启动耗时较长

<font color=red>**在首次运行oddasr时，它将从互联网下载多个模型文件，这需要相当长的时间，从10分钟到更长时间不等，具体取决于您的互联网带宽。同时你也需要为这些模型文件预留好至少8G的存储空间.**</font>

此外, 即使不是首次运行，oddasr服务器仍然<font color=red>**需要几分钟才能启动**</font>，因为默认配置下, OddASR采用了预加载模式启动, 以加快ASR请求的响应。

只有你看到了诸如下面这样的日志, 才代表 OddASR 已经初始化成功, 并启动起来了。

```bash
2025-07-25T08:22:08.093187031Z  * Running on all addresses (0.0.0.0)
2025-07-25T08:22:08.093201526Z  * Running on http://127.0.0.1:9002
2025-07-25T08:22:08.093213810Z  * Running on http://172.17.0.2:8101
2025-07-25T08:22:08.093226351Z Press CTRL+C to quit
```

#### 2) 硬盘存储需求较大

OddASR集成了多个不同类型的模型, 包括ASR模型/VAD检测模型/标点符号模型/角色分离模型. 这些模型都会占用比较大的硬盘空间(初次运行时还要下载), 因此如果你也硬盘空间吃紧的话, 可以考虑跟我一样指定一下模型下载后存储的位置

- Windows环境

```bash
set HF_ENDPOINT=https://hf-mirror.com
set HF_HOME=F:/ai_share/models
```

- Mac/Linux环境

```bash
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/data/ai_share/models
```

## 四、如何使用OddASR?

### 1. 文件ASR转写 API

直接将你的文件路径放在一个表单里, 然后以HTTP POST的方式发给 OddASR即可.

```python
def test_file(audio_path: str, output_format: str = "txt"):
    # 设置服务的 URL
    url = "http://127.0.0.1:9002/v1/asr"
    # 定义 hotwords
    hotwords = "小落 小落同学 奥德元 小奥"
    # 打开音频文件
    with open(audio_path, "rb") as audio_file:
        # 发送 POST 请求
        response = requests.post(url, files={"audio": audio_file}, data={"hotwords": hotwords, "mode": "file", "output_format": output_format})
        # 输出结果
        if response.status_code == 200:
            try:
                print("Recognition Result:", response.json()["text"])
            except ValueError:
                print("Non-JSON response:", response.text)  # Print the raw response
        else:
            print("Error:", response.text)  # Print the raw error message
```

具体的示例可参考: https://github.com/oddmeta/oddasr/blob/master/testAPI.py

转写后输出的格式支持三种格式:
- txt: 文本模式
- spk: 发言人模式
- srt: 字幕模式

具体的格式下面有示例, 可参考下面的内容。

### 2. 流式ASR转写 API

流式ASR转写以websocket的方式提供API接口, 整个API调用流程如下:

'''
    client --> server: connect
    client --> server: TCmdApppyAsrReq, msg_type = StartTranscription;
    server --> client: TCmdApplyAsrRes, msg_type = MSG_SUBSCRIBE_INIT_RES;
    client --> server: TCMDTranscribeReq, msg_type = MSG_TRANSCRIBE_REQ;
    server --> client: TCMDTranscribeRes, msg_type = MSG_TRANSCRIBE_RES;

    TCMDTranscribeReq
'''

具体的示例可参考: https://github.com/oddmeta/oddasr/blob/master/testStreamAPI.py

### 3. 一句话ASR转写 API

同文件ASR转写API, 但是输出格式只支持文本模式, 不支持发言人模式和字幕模式.

### 4. 测试脚本示例

- 测试脚本
	- **`testAPI.py`**：测试ASR API文件模式的示例客户端脚本。
	- **`testStreamAPI.py`**：测试ASR API流式模式的示例客户端脚本。
- 音频文件
	- **`test_cn_male9s.wav`**：用于测试的示例音频文件。
	- **`test_en_steve_jobs_10s.wav`**：用于测试的示例音频文件。
	- **`test_cn_16k-16bits-mono.wav`**：用于流式ASR测试的示例音频文件。


#### 1) 测试文件ASR转写 API

使用`testAPI.py`脚本测试API：

```bash
python testAPI.py test_en_steve_jobs_10s.wav txt
```

示例`curl`命令：

- 将音频文件发送到REST API

```bash
curl -X POST -F "audio=@path/to/audio.wav" http://127.0.0.1:12340/v1/asr
```

测试`test_cn_male_9s.wav`音频文件的示例`curl`命令：

```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:12340/v1/asr
```

仓库中有两个测试音频文件：

- `test_cn_male9s.wav`
- `test_en_steve_jobs_10s.wav`

您可以通过以下方式测试它们：
```bash
curl -X POST -F "audio=@test_cn_male_9s.wav" http://127.0.0.1:12340/v1/asr
curl -X POST -F "audio=@test_en_steve_jobs_10s.wav" http://127.0.0.1:12340/v1/asr
```

#### 2) 测试流式ASR转写 API

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


### 5. 示例输出

#### 1) 文本模式

```bash
是开始这个呃实时的一个转写。
对， 然后是转写的一个效果， 大概大概就是这个样子。 
然后的话那个在这里边你也可以去给他那个加一个人。 
比如说是嗯我随便给他取一个名字， 
就是连云端的还是自己算的连云端的吧。 
```

#### 2) 发言人模式

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

#### 3) SRT模式

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

## 五、自定义配置你自己的OddASR配置

关于OddASR自定义配置功能, 我一开始的想法是在命令行里加参数, 让用户可以直接以命令行参数的方式来自定义启动, 但是我要支持的参数实在太多了, 想想就放弃走命令行参数这条路了, 还是直接传配置文件来得直接一些。

因此, 现在版本的 OddASR 已经去掉了命令行参数自定义配置的功能, 改用了传配置文件。

### 1. 默认配置

默认安装下，oddasr会使用 0.0.0.0的地址，然后绑定一个9002的HTTP端口和一个8101的websocket端口。

主要的配置项如下：

- `HOST`：HTTP端口配置，默认端口号9002。用于文件ASR转写，以及一些demo和管理功能。
- `WS_PORT`：Websocket端口配置，默认端口号8101。用于流式ASR转写。
- `preload_model`: 启动时是否预加载模型，默认True，以便于在收到ASR转写请求后可以快速响应。加载模型比较慢，几秒到几十秒，看你CPU、内存硬件配置，以及加载的实例数。
- `enable_gpu`: 是否启用GPU，默认False，不使用GPU。
- `disable_stream`: 默认启用流式ASR转写，默认False。
- `concurrent_thread`: 并发线程数，默认为0，即默认以CPU核数启动线程。
- `max_instance`: 最大实例数，默认为1，也即只支持一路并发转写。如果你的硬件配置够，可以把最大实例数放到更大，让你的OddASR可以支持更多路并发。

### 2. 完整的配置项

具体的如下：

```python
DEFAULT_CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 9002,							# HTTP端口
    "WS_HOST": "0.0.0.0",
    "WS_PORT": 8101,						# Websocket端口
    "Debug": False,
    "odd_asr_cfg": {
        "preload_model": True,				# 启动时预加载模型，以便于在收到ASR转写请求后可以
        "enable_gpu": False,				# 默认不使用GPU
        "disable_stream": False,			# 默认启用流式ASR转写
        "concurrent_thread": 0,				# 默认以CPU核数启动线程
        "asr_stream_cfg": {
            'max_instance': 1,				# 最大流式ASR转写实例数
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
            'max_instance': 1,				# 最大文件ASR转写实例数
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
            'max_instance': 1,				# 最大一句话ASR转写实例数
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
            "path": "scripts/sensitivewords",	# 敏感词路径
        },
        "hotwords": {
            "path": "scripts/hotwords",			# 热词路径
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

## 七、待办事项

- [ ] 添加更多模型和功能。尤其是前两天看到FunASR-nano版本的模型出来了, 一直想去试试效果, 但一直没时间。
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

## 八、许可证

OddASR 项目没有任何许可证。
自由复制，没有任何附加条件！只需快乐编码！

