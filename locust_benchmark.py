from locust import HttpUser, task, between
import os

AUDIO_FILE = "test_cn_male_9s.wav"

class ASRUser(HttpUser):
    wait_time = between(0.5, 1.5)
    host = "http://localhost:9002"

    @task
    def openai_transcribe(self):
        if not os.path.exists(AUDIO_FILE):
            return
        with open(AUDIO_FILE, "rb") as f:
            files = {"file": (AUDIO_FILE, f, "audio/wav")}
            with self.client.post("/v1/audio/transcriptions", files=files, catch_response=True) as resp:
                if resp.status_code == 200:
                    resp.success()
                else:
                    resp.failure(f"status={resp.status_code}")

    @task(weight=2)
    def sentence_asr(self):
        if not os.path.exists(AUDIO_FILE):
            return
        with open(AUDIO_FILE, "rb") as f:
            files = {"audio": (AUDIO_FILE, f, "audio/wav")}
            with self.client.post("/v1/asr/sentence", files=files, catch_response=True) as resp:
                if resp.status_code == 200:
                    resp.success()
                else:
                    resp.failure(f"status={resp.status_code}")
