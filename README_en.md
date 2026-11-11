# OddASR - OpenAI API Compatible ASR Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12.0+](https://img.shields.io/badge/python-3.12.0.+-blue.svg)](https://www.python.org/downloads/)

OddASR is an OpenAI API compatible Automatic Speech Recognition (ASR) server that supports both offline and streaming transcription.

## Features

- ✅ **OpenAI API Compatible**: Drop-in replacement for OpenAI Whisper API
- ✅ **Multiple Response Formats**: text, srt, vtt, json, verbose_json, spk
- ✅ **Real-time Streaming**: WebSocket support for live audio processing with VAD
- ✅ **Offline Processing**: Batch transcription for audio files with custom models and backends
- ✅ **Voice Activity Detection**: Smart speech detection with Silero VAD
- ✅ **2-Pass ASR**: Combines streaming and offline models for low latency and high accuracy
- ✅ **Multiple Backend Support**: Paraformer, SenseVoice (sherpa-onnx), SenseVoice FunASR, Moonshine ASR, Qwen3-ASR models with custom model and backend support
- ✅ **Easy to Use**: Simple web interface and Python API
- ✅ **Dynamic Model Switching**: Switch backend models via frontend or API without restarting the service

## Quick Start

### Installation

Install directly:

```bash
pip install oddasr
```

Or build from source:

```bash
# Clone the repository
git clone https://github.com/oddmeta/oddasr.git
cd oddasr

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Configuration (Optional)

The server runs without a configuration file using the built-in `DEFAULT_CONFIG`. To customize, create `config.json` in the project root and override only the keys you need to modify.

### Basic Usage

Start the server:

```bash
oddasr-server
```

or with custom configuration:

```bash
oddasr-server --config config.json
```

The server will start on:
- **Web Interface**: http://localhost:9002
- **HTTP API**: http://localhost:9002/v1
- **WebSocket API**: ws://localhost:9003/v1/realtime

## Architecture

### 2-Pass ASR

OddASR uses a 2-pass ASR strategy:

1. **Streaming Pass**: Real-time transcription using streaming ASR model
2. **Offline Pass**: Final refinement using offline ASR model with punctuation

This combination provides both low latency and high accuracy.

### Supported Models

| Backend | Streaming | Offline | Punctuation | Speaker Diarization |
|---------|----------|---------|-------------|---------------------|
| Paraformer | paraformer-zh-streaming | paraformer-zh | ✓ | ✓ |
| SenseVoice (sherpa-onnx) | sherpa-onnx (built-in VAD) | sherpa-onnx (built-in VAD) | built-in | ✗ |
| SenseVoice FunASR | iic/SenseVoiceSmall | iic/SenseVoiceSmall | built-in | ✗ |
| Moonshine | moonshine/base | moonshine/base | ✓ | ✗ |
| Qwen3-ASR-0.6B | Qwen/Qwen3-ASR-0.6B | Qwen/Qwen3-ASR-0.6B | built-in | ✓ |
| Qwen3-ASR-1.7B | Qwen/Qwen3-ASR-1.7B | Qwen/Qwen3-ASR-1.7B | built-in | ✓ |

## API Usage

### Python Client

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:9002/v1",
    api_key="dummy"  # Not required but kept for compatibility
)

# Offline transcription
with open("audio.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="oddasr-2",
        model_type="paraformer-funasr",
        file=audio_file,
        response_format="text"  # text, srt, vtt, json, verbose_json, spk
    )
    print(transcript.text)
```

### cURL

```bash
curl -X POST http://localhost:9002/v1/audio/transcriptions \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  -F "model=oddasr-2" \
  -F "model_type=paraformer-funasr" \
  -F "response_format=text"
```

### WebSocket Streaming

```python
import asyncio
import websockets
import json
import base64

async def realtime_transcription():
    uri = "ws://localhost:9003/v1/realtime"
    
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            
            if data['type'] == 'conversation.item.input_audio_transcription.completed':
                print(f"Transcription: {data['transcript']}")
            elif data['type'] == 'response.audio_transcript.delta':
                print(f"Partial: {data['delta']}", end='\r')
            elif data['type'] == 'error':
                print(f"Error: {data['error']['message']}")

asyncio.run(realtime_transcription())
```

## Response Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| text | Plain text | Simple transcription |
| srt | SubRip subtitles | Video subtitles |
| vtt | WebVTT subtitles | Web video |
| json | Simple JSON | Programmatic processing |
| verbose_json | Detailed JSON with timestamps | Analysis and debugging |
| spk | Speaker diarization output | Speaker identification |

## Project Structure

```
oddasr/
├── api/                  # API handlers
├── logic/                # Business logic
│   ├── odd_asr_server.py       # WebSocket server
│   ├── odd_asr_stream_handler.py  # Stream handler
│   └── odd_asr_instance_pool.py    # Model instance pool
├── models/               # ASR models
│   ├── base_asr.py            # Base ASR interface
│   ├── paraformer_asr.py      # Paraformer FunASR implementation
│   ├── moonshine_asr.py       # Moonshine implementation
│   ├── sensevoice_onnx.py      # SenseVoice ONNX (sherpa-onnx) implementation
│   ├── sensevoice_small.py    # SenseVoiceSmall implementation
│   ├── qwen3_asr_06b.py       # Qwen3-ASR-0.6B implementation
│   ├── qwen3_asr_17b.py       # Qwen3-ASR-1.7B implementation
│   ├── realtime_asr.py        # Realtime ASR controller
│   └── punctuation.py         # Punctuation model
├── utils/                # Utilities
│   ├── audio.py              # Audio processing
│   ├── vad.py                # Voice Activity Detection
│   ├── formatters.py         # Response formatters
│   └── messages.py           # WebSocket messages
├── templates/            # Web templates
├── static/               # Static files
├── tests/                # Test files
├── app.py                # Main application
├── requirements.txt      # Dependencies
└── setup.py              # Packaging configuration
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_vad.py
```

### Code Structure

The codebase follows a clean architecture:

- **logic/**: Server and request handling
- **models/**: ASR model implementations (FunASR, Moonshine, SenseVoice, Qwen3-ASR)
- **utils/**: Audio processing, VAD, formatters

## Configuration

The server uses the built-in `DEFAULT_CONFIG` and does not require a configuration file to run. To customize, create `config.json` in the project root and override only the keys you need.

### Configuration Example

```
{
  "active_model_index": 0,
  "model_options": [
    {
      "model_type": "paraformer-funasr",
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
          "model": "iic/speech_eres2netv2_sv_zh-cn_16k-common",
          "revision": "v2.0.4",
          "enable": false
        }
      }
    },
    {
      "model_type": "sensevoice",
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
      "model_type": "sensevoice-funasr",
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
    "max_audio_samples": 480000
  }
}
```

### Configuration Options

#### Model Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `active_model_index` | Default active model option index | 0 |
| `model_options` | Available model configuration list | See DEFAULT_CONFIG |
| `model_options[].model_type` | ASR backend type identifier | paraformer-funasr |
| `model_options[].display_name` | Display name shown in frontend | Same as model_type |
| `model_options[].output_type` | Supported response formats for this backend | `["text"]` |
| `models.streaming.model` | Streaming model name | paraformer-zh-streaming |
| `models.streaming.max_instance` | Max streaming instances | 1 |
| `models.offline.model` | Offline model name | paraformer-zh |
| `models.offline.max_instance` | Max offline instances | 1 |

#### VAD Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `asr.vad_enabled` | Enable VAD | true |
| `asr.vad_use_model` | Use Silero VAD model | true |
| `asr.vad_model_threshold` | Speech detection threshold | 0.5 |
| `asr.vad_silence_duration` | Silence duration to trigger end (s) | 0.5 |
| `asr.vad_speech_padding` | Padding after speech (s) | 0.2 |
| `asr.vad_energy_threshold` | Energy mode threshold | 0.01 |

#### Server Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `server.max_connections` | Max WebSocket connections | 10 |
| `server.ping_interval` | WebSocket ping interval | 0 |
| `server.ping_timeout` | WebSocket ping timeout | 120 |

## License

MIT License - see LICENSE file for details

## Support

- GitHub: https://github.com/oddmeta/oddasr
- Documentation: https://oddmeta.net/docs/oddasr
- Issues: https://github.com/oddmeta/oddasr/issues

## Acknowledgments

- [FunASR](https://github.com/modelscope/FunASR) for excellent ASR models
- [Moonshine](https://github.com/usefulsensors/moonshine) for fast streaming ASR
- [SenseVoice](https://github.com/k2-fsa/sherpa-onnx/tree/main/sensevoice) for ONNX-optimized SenseVoice model
- [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) for Qwen3 speech recognition model
- [Silero VAD](https://github.com/snakers4/silero-vad) for voice activity detection
- OpenAI for the API design inspiration
