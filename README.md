# OddASR - 兼容 OpenAI API 的语音识别服务器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12.0+](https://img.shields.io/badge/python-3.12.0.+-blue.svg)](https://www.python.org/downloads/)

OddASR 是一个兼容 OpenAI API 的自动语音识别（ASR）服务器，支持离线转录和流式转录，采用 2-pass ASR 策略以提高准确性。

> 注意：
> - 首次运行时，会自动下载模型文件。模型文件会保存在 `models/` 目录下。
> - 模型文件大小较大，建议在有足够磁盘空间的环境运行。
> - 国内用户建议使用镜像加速下载模型文件。
>   - Windows: set HF_ENDPOINT=https://hf-mirror.com
>   - Linux/MacOS: export HF_ENDPOINT=https://hf-mirror.com
> - 本项目基于 Paraformer、Moonshine、SenseVoice、Qwen3-ASR 模型实现，若需要使用其他模型，请自行在配置文件中指定模型路径。

## 功能特性

- ✅ **OpenAI API 兼容**：可作为 OpenAI Whisper API 的替代方案（**中文准确率比 Whisper 高，英文准确率也比 Whisper 高，但英文延迟会高一些**）
- ✅ **多种响应格式**：支持 text、srt、vtt、json、verbose_json、diarized_json、spk。除spk是OddASR自定义格式，其他格式与 OpenAI API 兼容
- ✅ **实时流式识别**：支持 WebSocket 实时音频处理，集成 VAD 语音活动检测
- ✅ **文件流式识别**：网页端可选择本地音频文件，通过 WebSocket 以流式方式逐块发送并实时显示转写结果
- ✅ **离线处理**：支持批量音频文件转录，支持自定义模型和后端（最大支持的离线识别的音频文件大小从16M提升到50M）
- ✅ **语音活动检测**：采用 Silero VAD 实现智能语音检测
- ✅ **2-pass ASR**：结合流式和离线模型，兼顾低延迟和高准确率
- ✅ **多后端支持**：支持 Paraformer、SenseVoice (sherpa-onnx)、SenseVoice FunASR、Moonshine ASR、Qwen3-ASR 模型，支持自定义模型和后端
- ✅ **说话人识别**：支持说话人分离（Speaker Diarization），可指定说话人数量、上限、合并阈值与分离粒度，Paraformer 与 Qwen3-ASR 后端可用（详见 [说话人分离配置](docs/oddasr-speaker-diarization-config.md)）
- ✅ **Web 界面**：提供企业蓝主题网页 Demo，支持麦克风录音、文件流式、离线上传三种识别方式，支持音频播放预览
- ✅ **模型动态切换**：通过 `model` 参数（如 `oddasr2_qwen3-asr-0.6b`）在请求中指定后端模型，HTTP 和 WebSocket 均支持，无需重启服务
- ✅ **GPU 自动回退**：配置 `device=cuda` 时，若 CUDA 不可用自动回退到 CPU 并输出 warning，避免服务启动失败

## 快速开始

### 安装

直接安装：

```bash
pip install oddasr
```

或者从源码编译：

```bash
# 克隆仓库
git clone https://github.com/oddmeta/oddasr.git
cd oddasr

# 安装依赖
pip install -r requirements.txt
pip install -e .
```

### 配置（可选）

服务启动时无需配置文件，使用内置 `DEFAULT_CONFIG`。如需自定义，在项目根目录创建 `config.json`，只需覆盖需要修改的项即可：

```
{
  "active_model_index": 0,
  "model_options": [
    {
      "model_type": "paraformer-zh",
      "display_name": "FunASR (Paraformer)",
      "output_type": ["text", "srt", "vtt", "json", "verbose_json", "spk"],
      "options": {
        "streaming": {
          "model": "paraformer-zh-streaming",
          "revision": "v2.0.4",
          "device": "cpu",
          "max_instance": 1
        },
        "offline": {
          "model": "paraformer-zh",
          "revision": "v2.0.4",
          "device": "cpu",
          "max_instance": 1
        },
        "punc": {
          "model": "iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727",
          "revision": "v2.0.4"
        },
        "spk": {
          "model": "iic/speech_campplus_sv_zh-cn_16k-common",
          "enable": false,
          "preset_spk_num": 0,
          "max_num_spks": 15,
          "merge_thr": 0.78,
          "spk_mode": "punc_segment"
        }
      }
    },
    {
      "model_type": "sensevoice-onnx",
      "display_name": "SenseVoice",
      "output_type": ["text"],
      "options": {
        "streaming": {
          "model": "models/oddasr_model/model/model.int8.onnx",
          "device": "cpu",
          "max_instance": 1
        },
        "offline": {
          "model": "models/oddasr_model/model/model.int8.onnx",
          "device": "cpu",
          "max_instance": 1
        }
      }
    },
    {
      "model_type": "sensevoice-small",
      "display_name": "SenseVoice FunASR",
      "output_type": ["text"],
      "options": {
        "streaming": {
          "model": "iic/SenseVoiceSmall",
          "revision": "master",
          "device": "cpu",
          "max_instance": 1
        },
        "offline": {
          "model": "iic/SenseVoiceSmall",
          "revision": "master",
          "device": "cpu",
          "max_instance": 1
        }
      }
    }
  ],
  "vad": {
    "vad_use_model": true,
    "vad_model_name": "silero-vad",
    "vad_model_threshold": 0.5,
    "vad_device": "cpu",
    "vad_silence_duration": 1.0
  },
  "2pass": {
    "max_audio_samples": 80000
  }
}
```

详见 [配置](#配置) 部分。

### 基本用法

启动服务器：

```bash
oddasr-server
```

或使用自定义配置：

```bash
oddasr-server --config config.json
```

服务器启动后的访问地址：
- **Web 界面**：http://localhost:9002
- **HTTP API**：http://localhost:9002/v1
- **WebSocket API**：ws://localhost:9003/v1/realtime

Web 界面提供三种识别方式：
- **🌊 流式识别**：使用麦克风实时录音，通过 WebSocket 流式传输
- **📂 文件流式识别**：选择本地音频文件，通过 WebSocket 以流式方式逐块发送
- **📁 离线识别**：上传音频文件，通过 HTTP API 获取完整转写结果

## 架构

### 2-Pass ASR

OddASR 采用 2-pass ASR 策略：

1. **流式识别**：使用流式 ASR 模型进行实时转录
2. **离线优化**：使用离线 ASR 模型和标点模型进行最终优化

这种组合同时实现了低延迟和高准确率。

### 支持的模型

| 后端 | 流式识别 | 离线识别 | 标点 | 说话人识别 |
|------|---------|---------|------|-----------|
| Paraformer | paraformer-zh-streaming | paraformer-zh | ✓ | ✓ |
| SenseVoice (sherpa-onnx) | sherpa-onnx (内置 VAD) | sherpa-onnx (内置 VAD) | 内置 | ✗ |
| SenseVoice FunASR | iic/SenseVoiceSmall | iic/SenseVoiceSmall | 内置 | ✗ |
| Moonshine | moonshine/base | moonshine/base | ✓ | ✗ |
| Qwen3-ASR-0.6B | Qwen/Qwen3-ASR-0.6B | Qwen/Qwen3-ASR-0.6B | 内置 | ✓ |
| Qwen3-ASR-1.7B | Qwen/Qwen3-ASR-1.7B | Qwen/Qwen3-ASR-1.7B | 内置 | ✓ |


## API 使用方法

### Python 客户端

```
import openai

client = openai.OpenAI(
    base_url="http://localhost:9002/v1",
    api_key="dummy"  # 兼容需要，实际无需填写
)

# 离线转录（通过 model 参数指定后端模型）
with open("audio.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="oddasr2_paraformer-zh",  # 或 oddasr2_qwen3-asr-0.6b、oddasr2_sensevoice 等
        file=audio_file,
        response_format="text"  # text, srt, vtt, json, verbose_json, spk, diarized_json
    )
    print(transcript.text)
```

### cURL

```
curl -X POST http://localhost:9002/v1/audio/transcriptions \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  -F "model=oddasr2_paraformer-zh" \
  -F "response_format=text"
```

> `model` 参数支持 `oddasr2_{model_type}` 格式（如 `oddasr2_qwen3-asr-0.6b`、`oddasr2_sensevoice-onnx`），优先于 `model_type` 参数。若 `model` 无法识别，则回退到 `model_type`。

说话人分离（可指定说话人数量等参数，详见 [说话人分离配置](docs/oddasr-speaker-diarization-config.md)）：

```
curl -X POST http://localhost:9002/v1/audio/transcriptions \
  -H "Content-Type: multipart/form-data" \
  -F "file=@meeting.wav" \
  -F "model_type=paraformer-zh" \
  -F "response_format=diarized_json" \
  -F "preset_spk_num=2"          # 可选：强制 2 个说话人
  -F "max_num_spks=4"            # 可选：自动估计时的上限
  -F "merge_thr=0.78"            # 可选：合并相似说话人的余弦阈值
  -F "spk_mode=punc_segment"     # 可选：分离粒度
```

### WebSocket 流式识别

```
import asyncio
import websockets
import json
import base64

async def realtime_transcription():
    # 通过 URL 的 model 参数指定后端模型（可选，不传则使用默认模型）
    uri = "ws://localhost:9003/v1/realtime?model=oddasr2_qwen3-asr-0.6b"
    
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            
            if data['type'] == 'conversation.item.input_audio_transcription.completed':
                print(f"转录结果: {data['transcript']}")
            elif data['type'] == 'response.audio_transcript.delta':
                print(f"中间结果: {data['delta']}", end='\r')
            elif data['type'] == 'error':
                print(f"错误: {data['error']['message']}")

asyncio.run(realtime_transcription())
```

### 流式测试客户端

项目内置了流式转写测试程序，支持命令行参数：

```
# 基本用法
python tests/test_api_streaming.py tests/test.wav

# 指定 chunk 大小和服务器地址
python tests/test_api_streaming.py tests/test.wav --chunk-ms 300 --host 192.168.1.10 --port 9003

# 以最快速度发送（不模拟实时延迟）
python tests/test_api_streaming.py tests/test.wav --no-simulate-realtime
```

功能特点：
- 自动将音频重采样到 16kHz
- 支持自定义 chunk 时长（默认 600ms）
- 支持模拟实时发送或全速发送
- 显示发送进度、partial 中间结果和 final 最终结果

## 响应格式

| 格式 | 说明 | 使用场景 |
|------|------|----------|
| text | 纯文本 | 简单转录 |
| srt | SubRip 字幕 | 视频字幕 |
| vtt | WebVTT 字幕 | 网页视频 |
| json | 简单 JSON | 程序处理 |
| verbose_json | 带时间戳的详细 JSON | 分析调试 |
| spk | 说话人识别模型输出 | 说话人识别 |
| diarized_json | 带说话人分离的详细 JSON | 说话人识别 |

## 项目结构

```
oddasr/
├── app.py                     # 主程序入口
├── logic/                     # 业务逻辑
│   ├── odd_asr_server.py           # WebSocket 服务器
│   ├── odd_asr_stream_handler.py   # 流式处理器（OpenAI Realtime API 兼容）
│   ├── odd_asr_instance_pool.py    # ASR 模型实例池管理
│   └── odd_asr_global.py           # 全局状态
├── models/                    # ASR 模型
│   ├── base_asr.py                 # ASR 基类接口
│   ├── paraformer_asr.py           # Paraformer 实现（含 Cython 加速）
│   ├── moonshine_asr.py            # Moonshine 实现
│   ├── sensevoice_onnx.py           # SenseVoice ONNX (sherpa-onnx) 实现
│   ├── sensevoice_small.py        # SenseVoiceSmall 实现
│   ├── qwen3_asr_06b.py            # Qwen3-ASR-0.6B 实现
│   ├── qwen3_asr_17b.py            # Qwen3-ASR-1.7B 实现
│   ├── realtime_asr.py             # Realtime ASR 控制器
│   └── punctuation.py              # 标点模型
├── router/                    # Flask 路由
│   ├── api.py                      # REST API 路由
│   └── front.py                    # 前端页面路由
├── utils/                     # 工具函数
│   ├── audio.py                    # 音频处理（含重采样）
│   ├── vad.py                      # Silero VAD 语音活动检测
│   ├── formatters.py               # 响应格式化（text/srt/vtt/json）
│   ├── messages.py                 # WebSocket 消息格式（OpenAI 兼容）
│   └── model_manager.py            # 模型下载管理
├── templates/                 # Web 模板
│   └── index.html                  # 网页 Demo（Tab 布局、企业蓝主题）
├── static/                    # 静态文件
├── tests/                     # 测试文件
│   ├── test_api_offline.py         # 离线 API 集成测试
│   ├── test_api_streaming.py       # 流式 WebSocket 测试客户端
│   ├── test_vad.py                 # VAD 单元测试
│   └── test_realtime_asr.py        # Realtime ASR 测试
├── docs/                      # 文档
├── models/oddasr_model/       # 本地 ONNX 模型（SenseVoice）
├── config.json                # 用户自定义配置（可选）
├── requirements.txt           # 依赖列表
└── setup.py                   # 打包配置
```

## 开发

### 运行测试

```
# 运行所有测试
pytest tests/

# 运行指定测试
pytest tests/test_vad.py
```

### 代码结构

代码遵循清晰的架构设计：

- **logic/**：服务器和请求处理
- **models/**：ASR 模型实现（Paraformer、Moonshine、SenseVoice-ONNX、SenseVoice、Qwen3-ASR-1.7B、Qwen3-ASR-0.6B）
- **utils/**：音频处理、VAD、格式化工具

## 配置

服务使用内置 `DEFAULT_CONFIG` 启动，无需配置文件即可运行。如需自定义，在项目根目录创建 `config.json`，只需覆盖需要修改的项。

### 配置示例

```
{
  "active_model_index": 0,
  "model_options": [
    {
      "model_type": "paraformer-zh",
      "output_type": ["text", "srt", "vtt", "json", "verbose_json", "spk"],
      "options": {
        "streaming": {
          "model": "paraformer-zh-streaming",
          "device": "cpu",
          "max_instance": 1
        },
        "offline": {
          "model": "paraformer-zh",
          "device": "cpu",
          "max_instance": 1
        },
        "punc": {
          "model": "iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727",
          "revision": "v2.0.4"
        },
        "spk": {
          "model": "iic/speech_campplus_sv_zh-cn_16k-common",
          "enable": false,
          "preset_spk_num": 0,
          "max_num_spks": 15,
          "merge_thr": 0.78,
          "spk_mode": "punc_segment"
        }
      }
    },
    {
      "model_type": "sensevoice-onnx",
      "output_type": ["text"],
      "options": {
        "streaming": {
          "model": "models/oddasr_model/model/model.int8.onnx",
          "device": "cpu",
          "max_instance": 1
        },
        "offline": {
          "model": "models/oddasr_model/model/model.int8.onnx",
          "device": "cpu",
          "max_instance": 1
        }
      }
    }
  ],
  "vad": {
    "vad_use_model": true,
    "vad_model_name": "silero-vad",
    "vad_model_threshold": 0.5,
    "vad_device": "cpu",
    "vad_silence_duration": 1.0
  },
  "2pass": {
    "max_audio_samples": 80000
  }
}
```

### 配置参数说明

#### 模型配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `active_model_index` | 默认激活的模型选项索引 | 1 |
| `model_options` | 可用模型配置列表 | 见 DEFAULT_CONFIG |
| `model_options[].model_type` | ASR 后端类型标识 | paraformer-zh |
| `model_options[].display_name` | 前端显示的模型名称 | 同 model_type |
| `model_options[].output_type` | 该后端支持的响应格式 | `["text"]` |
| `model_options[].options.streaming.model` | 流式识别模型名称 | paraformer-zh-streaming |
| `model_options[].options.streaming.device` | 流式模型运行设备（`cpu`/`cuda`）| cpu |
| `model_options[].options.offline.model` | 离线识别模型名称 | paraformer-zh |
| `model_options[].options.offline.device` | 离线模型运行设备（`cpu`/`cuda`）| cpu |

> **GPU 自动回退**：配置 `device=cuda` 时，服务启动会自动检查 `torch.cuda.is_available()`。若 CUDA 不可用（如驱动不兼容、PyTorch 版本不匹配），自动回退到 `cpu` 并输出 warning，确保服务仍能启动。
| `model_options[].options.spk.enable` | 启用说话人识别（FunASR / Qwen3-ASR）| false |
| `model_options[].options.spk.preset_spk_num` | 强制说话人数量，0=自动估计，>0=指定数量 | 0 |
| `model_options[].options.spk.max_num_spks` | 自动估计时的说话人数量搜索上界 | 15 |
| `model_options[].options.spk.merge_thr` | 合并相似说话人的余弦阈值 | 0.78 |
| `model_options[].options.spk.spk_mode` | 说话人分离粒度：punc_segment/vad_segment/default | punc_segment |

> 说话人分离参数的详细说明与使用示例见 [docs/oddasr-speaker-diarization-config.md](docs/oddasr-speaker-diarization-config.md)。

#### VAD 配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `vad.vad_use_model` | 使用 Silero VAD 模型 | true |
| `vad.vad_model_threshold` | 语音检测阈值 | 0.5 |
| `vad.vad_silence_duration` | 触发结束说话的静音时长（秒）| 1.0 |
| `vad.vad_speech_padding` | 语音前后填充时长（秒）| 0.3 |
| `vad.vad_energy_threshold` | 能量模式阈值 | 0.01 |

#### 2-Pass 配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `2pass.max_audio_samples` | 最大音频采样数（约 5s@16kHz）| 80000 |

#### 服务器配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `server.max_connections` | 最大 WebSocket 连接数 | 50 |
| `server.ping_interval` | WebSocket ping 间隔（秒）| 30 |
| `server.ping_timeout` | WebSocket ping 超时（秒）| 300 |


## 许可证

MIT 许可证 - 详见 LICENSE 文件

## 技术支持

- GitHub：https://github.com/oddmeta/oddasr
- 文档：https://oddmeta.net/docs/oddasr
- 问题反馈：https://github.com/oddmeta/oddasr/issues

## 致谢

- [FunASR](https://github.com/modelscope/FunASR) - 优秀的 ASR 模型
- [Moonshine](https://github.com/usefulsensors/moonshine) - 快速流式 ASR
- [SenseVoice](https://github.com/k2-fsa/sherpa-onnx/tree/main/sensevoice) - ONNX优化SenseVoice模型
- [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) - 通义千问语音识别模型
- [Silero VAD](https://github.com/snakers4/silero-vad) - 语音活动检测
- OpenAI API 设计: https://developers.openai.com/api/docs/guides/speech-to-text
