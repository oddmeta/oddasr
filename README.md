<div align="center">

<h1>OddASR</h1>

<p>
  <strong>OpenAI API Compatible High-Performance Speech Recognition Server</strong>
</p>

<p>
  Offline Transcription · Real-time Streaming · 2-Pass ASR · Multi-Backend Dynamic Switching
</p>

<p>
  <a href="https://www.oddmeta.net" target="_blank">🏠 Official Website</a> ·
  <a href="https://asr.oddmeta.net" target="_blank">🌐 Live Demo</a> ·
  <a href="https://oddmeta.net/docs/oddasr" target="_blank">📖 Documentation</a>
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

## ✨ Features

- 🎯 **OpenAI API Compatible** — Drop-in replacement for OpenAI Whisper API with significantly better Chinese recognition accuracy
- 🌊 **Real-time Streaming** — WebSocket real-time audio processing with integrated Silero VAD
- 📁 **Offline Batch Transcription** — Supports audio files up to 50MB, 7 response formats
- 🔄 **2-Pass ASR** — Streaming recognition (low latency) + offline optimization (high accuracy)
- 🔌 **Multi-Backend Support** — Paraformer, SenseVoice (ONNX/FunASR), Moonshine, Qwen3-ASR (0.6B/1.7B)
- 🗣️ **Speaker Diarization** — Configurable speaker count and merge threshold
- ⚡ **Dynamic Model Switching** — Switch backends in real time via the `model` parameter in HTTP / WebSocket requests without restart
- 🛡️ **GPU Auto-Fallback** — Automatically falls back to CPU when `cuda` is unavailable
- 🖥️ **Web Interface** — Enterprise-blue themed demo supporting microphone recording, file streaming, and offline upload

---

## 🚀 Quick Start

### Option 1: PyPI Install (Recommended)

```bash
pip install oddasr

# Start the server
oddasr-server
```

### Option 2: Run from Source

```bash
git clone https://github.com/oddmeta/oddasr.git
cd oddasr
pip install -r requirements.txt
pip install -e .

# Start the server
oddasr-server
# or with custom configuration
oddasr-server --config config.json
```

Once the server is running:

| Endpoint | Address |
|------|------|
| 🌐 Web Interface | http://localhost:9002 |
| 📡 HTTP API | http://localhost:9002/v1/audio/transcriptions |
| 🔌 WebSocket API | ws://localhost:9003/v1/realtime |
| 📋 Model List | http://localhost:9002/v1/models |

> On the first run, model files will be automatically downloaded to the `models/` directory. Users in mainland China are recommended to set a mirror for faster downloads:
> ```bash
> # Windows
> set HF_ENDPOINT=https://hf-mirror.com
> # Linux/macOS
> export HF_ENDPOINT=https://hf-mirror.com
> ```

---

## 📐 Architecture

```
┌─────────────────────────────────────────────┐
│           Clients (Web / API / SDK)          │
│   Browser · Python OpenAI SDK · cURL · WebSocket │
└──────────────────┬──────────────────────────┘
                   │ HTTP / WebSocket
┌──────────────────▼──────────────────────────┐
│              OddASR Service Layer            │
│  ┌──────────────┐      ┌─────────────────┐  │
│  │  Flask HTTP  │      │ WebSocket Server │  │
│  │  /v1/audio/  │      │ /v1/realtime    │  │
│  └──────────────┘      └─────────────────┘  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              ASR Core Engine                 │
│  ┌─────────────────────────────────────┐    │
│  │  2-Pass ASR                         │    │
│  │  ┌────────────┐    ┌──────────────┐ │    │
│  │  │ Streaming  │───→│   Offline    │ │    │
│  │  │ (low latency)    │ (high accuracy) │    │
│  │  └────────────┘    └──────────────┘ │    │
│  └─────────────────────────────────────┘    │
│  ┌────────────┐ ┌────────┐ ┌──────────┐    │
│  │  VAD       │ │ Punc   │ │ Spk      │    │
│  │ Silero VAD │ │ Model  │ │ Diariz.  │    │
│  └────────────┘ └────────┘ └──────────┘    │
└─────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           Multi-Backend Model Support        │
│  Paraformer · SenseVoice · Moonshine ·       │
│  Qwen3-ASR (0.6B/1.7B)                       │
└─────────────────────────────────────────────┘
```

---

## 🛠️ Supported Backends

| Backend | Streaming | Offline | Punctuation | Speaker Diarization | Example Model ID |
|------|:--------:|:--------:|:----:|:----------:|-------------|
| Paraformer (FunASR) | ✓ | ✓ | ✓ | ✓ | `oddasr2_paraformer-zh` |
| SenseVoice (sherpa-onnx) | ✓ | ✓ | Built-in | ✗ | `oddasr2_sensevoice-onnx` |
| SenseVoice (FunASR) | ✓ | ✓ | Built-in | ✗ | `oddasr2_sensevoice-small` |
| Moonshine | ✓ | ✓ | ✓ | ✗ | `oddasr2_moonshine` |
| Qwen3-ASR-0.6B | ✓ | ✓ | Built-in | ✓ | `oddasr2_qwen3-asr-0.6b` |
| Qwen3-ASR-1.7B | ✓ | ✓ | Built-in | ✓ | `oddasr2_qwen3-asr-1.7b` |

---

## 📡 API Usage

### Python Client (Offline Transcription)

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:9002/v1",
    api_key="dummy"  # Required for compatibility, not actually used
)

with open("audio.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="oddasr2_paraformer-zh",  # or oddasr2_qwen3-asr-0.6b, etc.
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

### WebSocket Real-time Transcription

```python
import asyncio, websockets, json

async def stream():
    uri = "ws://localhost:9003/v1/realtime?model=oddasr2_qwen3-asr-0.6b"
    async with websockets.connect(uri) as ws:
        async for msg in ws:
            data = json.loads(msg)
            if data['type'] == 'conversation.item.input_audio_transcription.completed':
                print(f"Result: {data['transcript']}")
            elif data['type'] == 'response.audio_transcript.delta':
                print(f"Partial: {data['delta']}", end='\r')

asyncio.run(stream())
```

---

## 📋 Response Formats

| Format | Description | Use Case |
|------|------|----------|
| `text` | Plain text | Simple transcription |
| `srt` | SubRip subtitles | Video subtitles |
| `vtt` | WebVTT subtitles | Web video |
| `json` | Simple JSON | Programmatic processing |
| `verbose_json` | Detailed JSON with timestamps | Analysis and debugging |
| `spk` | Speaker diarization raw output | Speaker analysis |
| `diarized_json` | JSON with speaker diarization | Meeting minutes |

---

## ⚙️ Configuration

The server starts with the built-in `DEFAULT_CONFIG` and requires no configuration file to run. To customize, create a `config.json` in the project root and override only the keys you need:

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

### Key Configuration Parameters

| Parameter | Description | Default |
|------|------|--------|
| `active_model_index` | Default active model option index | `0` |
| `model_options[].options.streaming.device` | Streaming model device (`cpu`/`cuda`) | `cpu` |
| `model_options[].options.offline.device` | Offline model device (`cpu`/`cuda`) | `cpu` |
| `model_options[].options.spk.enable` | Enable speaker diarization | `false` |
| `vad.vad_use_model` | Use Silero VAD model | `true` |
| `vad.vad_silence_duration` | Silence duration to trigger end (seconds) | `1.0` |
| `2pass.max_audio_samples` | Maximum audio samples (approx. 5s@16kHz) | `80000` |
| `server.max_connections` | Maximum WebSocket connections | `50` |

> For detailed speaker diarization configuration, see [docs/oddasr-speaker-diarization-config.md](docs/oddasr-speaker-diarization-config.md)

---

## 📁 Project Structure

```
oddasr/
├── app.py                      # Main application entry
├── logic/                      # Business logic
│   ├── odd_asr_server.py       # WebSocket server
│   ├── odd_asr_stream_handler.py  # Stream handler (OpenAI Realtime API compatible)
│   ├── odd_asr_instance_pool.py   # ASR model instance pool manager
│   └── odd_asr_global.py       # Global state
├── models/                     # ASR model implementations
│   ├── base_asr.py             # Base ASR interface
│   ├── paraformer_asr.py       # Paraformer implementation (Cython accelerated)
│   ├── sensevoice_onnx.py      # SenseVoice ONNX (sherpa-onnx)
│   ├── sensevoice_small.py     # SenseVoice FunASR
│   ├── moonshine_asr.py        # Moonshine
│   ├── qwen3_asr_06b.py        # Qwen3-ASR-0.6B
│   ├── qwen3_asr_17b.py        # Qwen3-ASR-1.7B
│   ├── realtime_asr.py         # Realtime ASR controller
│   └── punctuation.py          # Punctuation model
├── router/                     # Flask routes
│   ├── api.py                  # REST API routes
│   └── front.py                # Frontend page routes
├── utils/                      # Utility modules
│   ├── audio.py                # Audio processing (with resampling)
│   ├── vad.py                  # Silero VAD voice activity detection
│   ├── formatters.py           # Response formatters (text/srt/vtt/json)
│   ├── messages.py             # WebSocket message format (OpenAI compatible)
│   └── model_manager.py        # Model download manager
├── templates/                  # Web templates
├── static/                     # Static assets
├── tests/                      # Test files
├── docs/                       # Documentation
└── config.json                 # User custom configuration (optional, overrides DEFAULT_CONFIG)
```

---

## 🧪 Development

### Run Tests

```bash
pytest tests/               # All tests
pytest tests/test_vad.py    # VAD unit tests
python tests/test_api_streaming.py tests/audio.wav   # Streaming integration test
```

### Cython Compilation

Performance-critical modules (`logic/`, `models/`, `utils/`) support Cython compilation for acceleration:

```bash
python build.py        # Compile .py → .pyx → .pyd
python build.py clean  # Clean build artifacts
```

---

## 📬 Contact Us

| Channel | Handle |
|---------|--------|
| WeChat Official Account | 奥德元 |
| WeChat | oddmeta |
| Weibo | [oddmeta](https://weibo.com/oddmeta) |
| Twitter / X | [oddmet](https://x.com/oddmet) |

---

## 📄 License

[MIT](LICENSE)

---

<div align="center">

Made with ❤️ by [OddMeta](https://oddmeta.net)

</div>
