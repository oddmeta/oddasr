## Flask server binding IP & port
HOST = "127.0.0.1"
HOST = "0.0.0.0"
PORT = 12345
PORT = 7501
PORT = 8701
PORT = 9002

## WebSocket server binding IP & port
WS_HOST = "127.0.0.1"
WS_HOST = "0.0.0.0"
WS_PORT = 8101

## working mode - Debug mode: True/False， Release mode: False/True
Debug = False

odd_asr_cfg = {
    ## load model and allocate memory on startup
    "preload_model": True,
    ## enable gpu
    "enable_gpu": False,
    ## disable stream mode ASR
    "disable_stream": False,
    ## concurrent threads, 0 auto detect CPU cores
    "concurrent_thread": 0,
    ## asr stream config
    "asr_stream_cfg": {
        'max_instance': 1, 
        'save_audio': False,
        'punct_mini_len': 10, 
        'punct_time_mini_force_trigger': 3,
        'free_resource_timeout': 5,         # auto free resource if N seconds without receiving audio
        'force_final_result': 20,           # force final result after N seconds
        'vad_threshold': 0.8,               # vad_threshold
        'vad_min_speech_duration': 300,     # vad_min_speech_duration(ms)
        'vad_min_silence_duration': 200     # vad_min_silence_duration(ms)
        },

    ## asr file config
    "asr_file_cfg": { 'max_instance':1, 'save_audio': False },
    ## asr sentence config
    "asr_sentence_cfg": {
        'max_instance': 4, 
        'save_audio': False,
        'punct_mini_len': 10, 
        'punct_time_mini_force_trigger': 3,
        'free_resource_timeout': 5,         # auto free resource if N seconds without receiving audio
        'force_final_result': 20,           # force final result after N seconds
        'vad_threshold': 0.8,               # vad_threshold
        'vad_min_speech_duration': 300,     # vad_min_speech_duration(ms)
        'vad_min_silence_duration': 200     # vad_min_silence_duration(ms)
        },
    ## HTTPS configuration
    "enable_https": False,
    "ssl_cert_path": "scripts/cert.pem",
    "ssl_key_path": "scripts/key.pem",
}

odd_asr_slp_cfg = {
    "sensitive_words": {
        "path": "scripts/sensitivewords",
    }, 
    "hotwords": {
        "path": "scripts/hotwords",
    }
}

db_cfg = {
    "db_engine": "sqlite",
    "db_name": "oddasr.db",
    "db_user": "",
    "db_password": "",
    "db_host": "",
    "db_port": "",
}

## redis config
redis_cfg = {
    "redis_enabled": False,
    "redis_host": "127.0.0.1",
    "redis_port": 7379,
    "redis_password": "",
}

## log config
log_file = "oddasr.log"
log_path = "logs/"
log_level = 10 # 10-debug 20-info 30-warn 40-error 50-crit

## token authertication config
asr={'liveasr':'', 'appid':'oddasrtest', 'secret':'oddasrtest'}
Users = 'oddasr_users.json'

## OpenAI 兼容 API Key 配置
## 空字符串表示不鉴权，字符串表示单个 key，列表表示多个 key
openai_api_key = ""
