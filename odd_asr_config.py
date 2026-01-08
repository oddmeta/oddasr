import json
import os

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# 默认配置
DEFAULT_CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 9002,
    "WS_HOST": "0.0.0.0",
    "WS_PORT": 8101,
    "Debug": False,
    "odd_asr_cfg": {
        "preload_model": True,
        "enable_gpu": False,
        "disable_stream": False,
        "concurrent_thread": 0,
        "asr_stream_cfg": {
            'max_instance': 1,
            'save_audio': False,
            'punct_mini_len': 10,
            'punct_time_mini_force_trigger': 3,
            'free_resource_timeout': 5,
            'force_final_result': 20,
            'vad_threshold': 0.8,
            'vad_min_speech_duration': 300,
            'vad_min_silence_duration': 200
        },
        "asr_file_cfg": { 'max_instance':1, 'save_audio': False },
        "asr_sentence_cfg": {
            'max_instance': 1,
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
            "path": "scripts/sensitivewords",
        },
        "hotwords": {
            "path": "scripts/hotwords",
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

# 加载配置
def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        # 如果配置文件不存在，使用默认配置并创建配置文件
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG
    except Exception as e:
        print(f"Error loading config file: {e}")
        return DEFAULT_CONFIG

# 加载配置
config_data = load_config()

# 将配置项导出为模块级变量，保持原有接口不变
HOST = config_data.get("HOST", DEFAULT_CONFIG["HOST"])
PORT = config_data.get("PORT", DEFAULT_CONFIG["PORT"])
WS_HOST = config_data.get("WS_HOST", DEFAULT_CONFIG["WS_HOST"])
WS_PORT = config_data.get("WS_PORT", DEFAULT_CONFIG["WS_PORT"])
Debug = config_data.get("Debug", DEFAULT_CONFIG["Debug"])

odd_asr_cfg = config_data.get("odd_asr_cfg", DEFAULT_CONFIG["odd_asr_cfg"])
odd_asr_slp_cfg = config_data.get("odd_asr_slp_cfg", DEFAULT_CONFIG["odd_asr_slp_cfg"])
db_cfg = config_data.get("db_cfg", DEFAULT_CONFIG["db_cfg"])
redis_cfg = config_data.get("redis_cfg", DEFAULT_CONFIG["redis_cfg"])

log_file = config_data.get("log_file", DEFAULT_CONFIG["log_file"])
log_path = config_data.get("log_path", DEFAULT_CONFIG["log_path"])
log_level = config_data.get("log_level", DEFAULT_CONFIG["log_level"])

asr = config_data.get("asr", DEFAULT_CONFIG["asr"])
Users = config_data.get("Users", DEFAULT_CONFIG["Users"])