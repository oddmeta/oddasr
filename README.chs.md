<div align="center">

<h1>OddASR</h1>

<p>
  <strong>兼容 OpenAI API 的高性能语音识别服务器</strong>
</p>

<p>
  离线转录 · 实时流式 · 2-Pass ASR · 多后端动态切换
</p>

<p>
  <a href="https://www.oddmeta.net" target="_blank">🏠 官方网站</a> ·
  <a href="https://asr.oddmeta.net" target="_blank">🌐 在线演示</a> ·
  <a href="https://oddmeta.net/docs/oddasr" target="_blank">📖 文档中心</a>
</p>

<p>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://pypi.org/project/oddasr/"><img src="https://img.shields.io/badge/pypi-oddasr-blue.svg" alt="PyPI"></a>
</p>

<p>
  <a href="README.md">English</a> · <a href="README.chs.md">中文</a>
</p>

</div>

---

## ✨ 功能特性

- 🎯 **OpenAI API 兼容** — 可作为 OpenAI Whisper API 的即插即用替代方案，中文识别准确率显著优于 Whisper
- 🌊 **实时流式识别** — WebSocket 实时音频处理，集成 Silero VAD 语音活动检测
- 📁 **离线批量转录** — 支持最大 50MB 音频文件，7 种响应格式
- 🔄 **2-Pass ASR** — 流式识别（低延迟）+ 离线优化（高准确率）
- 🔌 **多后端支持** — Paraformer、SenseVoice (ONNX/FunASR)、Moonshine、Qwen3-ASR (0.6B/1.7B)
- 🗣️ **说话人分离** — 支持 Speaker Diarization，可指定说话人数量与合并阈值
- ⚡ **模型动态切换** — HTTP / WebSocket 请求中通过 `model` 参数实时切换后端，无需重启
- 🛡️ **GPU 自动回退** — 配置 `cuda` 不可用时自动回退 CPU，保证服务可用
- 🖥️ **Web 界面** — 企业蓝主题 Demo，支持麦克风录音、文件流式、离线上传三种方式

---

## 🚀 快速开始

### 方式一：PyPI 安装（推荐）

```bash
pip install oddasr

# 启动服务
oddasr-server
```

### 方式二：源码运行

```bash
git clone https://github.com/oddmeta/oddasr.git
cd oddasr
pip install -r requirements.txt
pip install -e .

# 启动服务
oddasr-server
# 或指定配置
oddasr-server --config config.json
```

服务启动后：

| 端点 | 地址 |
|------|------|
| 🌐 Web 界面 | http://localhost:9002 |
| 📡 HTTP API | http://localhost:9002/v1/audio/transcriptions |
| 🔌 WebSocket API | ws://localhost:9003/v1/realtime |
| 📋 模型列表 | http://localhost:9002/v1/models |

> 首次运行会自动下载模型文件到 `models/` 目录。国内用户建议设置镜像加速：
> ```bash
> # Windows
> set HF_ENDPOINT=https://hf-mirror.com
> # Linux/macOS
> export HF_ENDPOINT=https://hf-mirror.com
> ```

---

## 📐 技术架构

```
┌─────────────────────────────────────────────┐
│              客户端（Web / API / SDK）         │
│   浏览器 · Python OpenAI SDK · cURL · WebSocket │
└──────────────────┬──────────────────────────┘
                   │ HTTP / WebSocket
┌──────────────────▼──────────────────────────┐
│              OddASR 服务层                   │
│  ┌──────────────┐      ┌─────────────────┐  │
│  │  Flask HTTP  │      │ WebSocket Server │  │
│  │  /v1/audio/  │      │ /v1/realtime    │  │
│  └──────────────┘      └─────────────────┘  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              ASR 核心引擎                    │
│  ┌─────────────────────────────────────┐    │
│  │  2-Pass ASR                         │    │
│  │  ┌────────────┐    ┌──────────────┐ │    │
│  │  │ Streaming  │───→│   Offline    │ │    │
│  │  │  (低延迟)   │    │  (高准确率)   │ │    │
│  │  └────────────┘    └──────────────┘ │    │
│  └─────────────────────────────────────┘    │
│  ┌────────────┐ ┌────────┐ ┌──────────┐    │
│  │  VAD 检测   │ │ 标点恢复 │ │ 说话人分离 │    │
│  │ Silero VAD │ │ Punc   │ │ Spk      │    │
│  └────────────┘ └────────┘ └──────────┘    │
└─────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              多后端模型支持                   │
│  Paraformer · SenseVoice · Moonshine ·      │
│  Qwen3-ASR (0.6B/1.7B)                      │
└─────────────────────────────────────────────┘
```

---

## 🛠️ 支持的后端模型

| 后端 | 流式识别 | 离线识别 | 标点 | 说话人分离 | 模型 ID 示例 |
|------|:--------:|:--------:|:----:|:----------:|-------------|
| Paraformer (FunASR) | ✓ | ✓ | ✓ | ✓ | `oddasr2_paraformer-zh` |
| SenseVoice (sherpa-onnx) | ✓ | ✓ | 内置 | ✗ | `oddasr2_sensevoice-onnx` |
| SenseVoice (FunASR) | ✓ | ✓ | 内置 | ✗ | `oddasr2_sensevoice-small` |
| Moonshine | ✓ | ✓ | ✓ | ✗ | `oddasr2_moonshine` |
| Qwen3-ASR-0.6B | ✓ | ✓ | 内置 | ✓ | `oddasr2_qwen3-asr-0.6b` |
| Qwen3-ASR-1.7B | ✓ | ✓ | 内置 | ✓ | `oddasr2_qwen3-asr-1.7b` |

---

## 📡 API 使用

### Python 客户端（离线转录）

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:9002/v1",
    api_key="dummy"  # 兼容需要，实际无需填写
)

with open("audio.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="oddasr2_paraformer-zh",  # 或 oddasr2_qwen3-asr-0.6b 等
        file=audio_file,
        response_format="text"  # text / srt / vtt / json / verbose_json / diarized_json / spk
    )
    print(transcript.text)
```

### cURL

```bash
curl -X POST http://localhost:9002/v1/audio/transcriptions \
  -F "file=@audio.wav" \
  -F "model=oddasr2_paraformer-zh" \
  -F "response_format=text"
```

### WebSocket 实时转录

```python
import asyncio, websockets, json

async def stream():
    uri = "ws://localhost:9003/v1/realtime?model=oddasr2_qwen3-asr-0.6b"
    async with websockets.connect(uri) as ws:
        async for msg in ws:
            data = json.loads(msg)
            if data['type'] == 'conversation.item.input_audio_transcription.completed':
                print(f"结果: {data['transcript']}")
            elif data['type'] == 'response.audio_transcript.delta':
                print(f"中间: {data['delta']}", end='\r')

asyncio.run(stream())
```

---

## 📋 响应格式

| 格式 | 说明 | 适用场景 |
|------|------|----------|
| `text` | 纯文本 | 简单转录 |
| `srt` | SubRip 字幕 | 视频字幕 |
| `vtt` | WebVTT 字幕 | 网页视频 |
| `json` | 简单 JSON | 程序处理 |
| `verbose_json` | 带时间戳的详细 JSON | 分析调试 |
| `spk` | 说话人识别原始输出 | 说话人分析 |
| `diarized_json` | 带说话人分离的 JSON | 会议纪要 |

---

## ⚙️ 配置

服务使用内置 `DEFAULT_CONFIG` 启动，无需配置文件即可运行。如需自定义，在项目根目录创建 `config.json`，仅覆盖需要修改的项：

```json
{
  "active_model_index": 0,
  "model_options": [
    {
      "model_type": "paraformer-zh",
      "display_name": "FunASR (Paraformer)",
      "output_type": ["text", "srt", "vtt", "json", "verbose_json", "spk"],
      "options": {
        "streaming": { "model": "paraformer-zh-streaming", "device": "cpu", "max_instance": 1 },
        "offline":   { "model": "paraformer-zh", "device": "cpu", "max_instance": 1 },
        "punc":      { "model": "iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727" },
        "spk":       { "enable": false, "preset_spk_num": 0, "max_num_spks": 15, "merge_thr": 0.78 }
      }
    }
  ],
  "vad": {
    "vad_use_model": true,
    "vad_model_threshold": 0.5,
    "vad_silence_duration": 1.0
  },
  "2pass": {
    "max_audio_samples": 80000
  }
}
```

### 关键配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `active_model_index` | 默认激活的模型选项索引 | `0` |
| `model_options[].options.streaming.device` | 流式模型运行设备 (`cpu`/`cuda`) | `cpu` |
| `model_options[].options.offline.device` | 离线模型运行设备 (`cpu`/`cuda`) | `cpu` |
| `model_options[].options.spk.enable` | 启用说话人分离 | `false` |
| `vad.vad_use_model` | 使用 Silero VAD 模型 | `true` |
| `vad.vad_silence_duration` | 触发结束的静音时长（秒） | `1.0` |
| `2pass.max_audio_samples` | 最大音频采样数（约 5s@16kHz） | `80000` |
| `server.max_connections` | 最大 WebSocket 连接数 | `50` |

> 说话人分离详细配置见 [docs/oddasr-speaker-diarization-config.md](docs/oddasr-speaker-diarization-config.md)

---

## 📁 项目结构

```
oddasr/
├── app.py                      # 主程序入口
├── logic/                      # 业务逻辑
│   ├── odd_asr_server.py       # WebSocket 服务器
│   ├── odd_asr_stream_handler.py  # 流式处理器（OpenAI Realtime API 兼容）
│   ├── odd_asr_instance_pool.py   # ASR 模型实例池管理
│   └── odd_asr_global.py       # 全局状态
├── models/                     # ASR 模型实现
│   ├── base_asr.py             # ASR 基类接口
│   ├── paraformer_asr.py       # Paraformer 实现（Cython 加速）
│   ├── sensevoice_onnx.py      # SenseVoice ONNX (sherpa-onnx)
│   ├── sensevoice_small.py     # SenseVoice FunASR
│   ├── moonshine_asr.py        # Moonshine
│   ├── qwen3_asr_06b.py        # Qwen3-ASR-0.6B
│   ├── qwen3_asr_17b.py        # Qwen3-ASR-1.7B
│   ├── realtime_asr.py         # Realtime ASR 控制器
│   └── punctuation.py          # 标点模型
├── router/                     # Flask 路由
│   ├── api.py                  # REST API 路由
│   └── front.py                # 前端页面路由
├── utils/                      # 工具模块
│   ├── audio.py                # 音频处理（含重采样）
│   ├── vad.py                  # Silero VAD 语音活动检测
│   ├── formatters.py           # 响应格式化（text/srt/vtt/json）
│   ├── messages.py             # WebSocket 消息格式（OpenAI 兼容）
│   └── model_manager.py        # 模型下载管理
├── templates/                  # Web 模板
├── static/                     # 静态资源
├── tests/                      # 测试文件
├── docs/                       # 文档
└── config.json                 # 用户自定义配置（可选，覆盖 DEFAULT_CONFIG）
```

---

## 🧪 开发

### 运行测试

```bash
pytest tests/               # 全部测试
pytest tests/test_vad.py    # VAD 单元测试
python tests/test_api_streaming.py tests/audio.wav   # 流式集成测试
```

### Cython 编译

性能关键模块（`logic/`、`models/`、`utils/`）支持 Cython 编译加速：

```bash
python build.py        # 编译 .py → .pyx → .pyd
python build.py clean  # 清理编译产物
```

---

## 📬 联系我们

| 渠道 | 账号 |
|------|------|
| 微信公众号 | 奥德元 |
| 微信 | oddmeta |
| 微博 | [oddmeta](https://weibo.com/oddmeta) |
| Twitter / X | [oddmet](https://x.com/oddmet) |

---

## 📄 License

[MIT](LICENSE)

---

<div align="center">

Made with ❤️ by [OddMeta](https://oddmeta.net)

</div>
