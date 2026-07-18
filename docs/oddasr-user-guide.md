# OddASR 2.x 版本说明

## 最新版本特性

本文主要介绍pypi安装 OddAsr 的快速使用方法。

### 核心特性

- **多模型支持**：Paraformer, Moonshine, SenseVoice, SenseVoice FunASR 等模型
- **VAD 智能检测**：自动检测语音结束，无需手动提交音频
- **WebSocket 流式输出**：实时获取部分识别结果
- **OpenAI API 兼容**：直接替换 Whisper API，无需修改代码

## 快速开始

### 安装

```bash
pip install oddasr
```

### 启动

```bash
oddasr-server
```

服务启动后：
- HTTP API: http://localhost:9002/v1
- WebSocket: ws://localhost:9003/v1/realtime

> 无需 `config.json` 配置文件，服务使用内置 `DEFAULT_CONFIG` 启动。如需自定义，创建 `config.json` 覆盖需要修改的项即可。切换模型时若配置文件不存在会自动创建。

## 使用 OddASR

支持OpenAI兼容接口。建议使用OpenAI API接口来调用。

### Python 客户端

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:9002/v1",
    api_key="dummy"
)

with open("audio.wav", "rb") as f:
    result = client.audio.transcriptions.create(
        model="oddasr-2",
        response_format="text",
        model_type="paraformer-funasr",
        file=f
    )
    print(result.text)
```

## 版本历史

### v2.x (当前)
- 全新 2-Pass ASR 架构
- 支持 Paraformer, Moonshine ONNX, SenseVoice ONNX, SenseVoiceSmall 多后端
- 前端动态加载模型选项，支持 API 切换模型（无需重启）
- Silero VAD 语音活动检测
- WebSocket 流式输出
- OpenAI API 完全兼容

### v1.x (已弃用)
- 单遍识别
- 简化标点处理
- 基础 WebSocket 支持

## 系统要求

- Python 3.8+
- CPU: 推荐 4 核以上
- 内存: 6GB+ (取决于并发数)
- 磁盘: 3GB+ (模型存储)

## 常见问题

### 首次运行需要下载模型吗？

是的，首次运行需要下载 ASR 模型。可以通过设置 HuggingFace 镜像加速：

Windows 环境下，设置镜像为：

```bash
set HF_ENDPOINT=https://hf-mirror.com
```

Linux/MacOS 环境下，设置镜像为：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 支持 GPU 加速吗？

支持，在配置中设置 `"device": "cuda:0"`：

```json
{
  "models": {
    "streaming": { "device": "cuda:0" },
    "offline": { "device": "cuda:0" }
  }
}
```

默认模型为 FunASR (Paraformer)。默认 VAD 模型为 Silero VAD。默认返回格式为 text。默认使用 CPU。

###### 如何调整识别灵敏度？

调整 VAD 参数：

```json
{
  "asr": {
    "vad_silence_duration": 0.5,   // 静音后多久触发
    "vad_speech_padding": 0.2,     // 语音结束后缓冲
    "vad_model_threshold": 0.5      // 语音检测阈值
  }
}
```

## 获取帮助

- 文档：[docs/](docs/)
- 问题反馈：[GitHub Issues](https://github.com/oddmeta/oddasr/issues)
- 完整 API 文档：[oddasr-api-guideline.md](oddasr-api-guideline.md)
- 贡献指南：[CONTRIBUTING.md](CONTRIBUTING.md)