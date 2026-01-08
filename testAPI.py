import requests

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


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Your WAV file need to recoginze to text.")
    parser.add_argument("audio_path", type=str, help="file path of your input WAV.")
    parser.add_argument("output_format", type=str, help="output format, support: txt, spk or srt.")
    args = parser.parse_args()

    # test command:  python testAPI VCS-20200916175424.wav spk
    file = args.audio_path
    print(f"Current working directory: {os.getcwd()}")
    print(f"Full file path: {os.path.abspath(file)}")
    if not os.path.exists(file):
        print(f"File not found: {file}")
        exit(1) 

    fmt = args.output_format
    if fmt not in ["txt", "spk", "srt"]:
        print(f"output_format must be txt, spk or srt: {fmt}")
        exit(1)

    test_file(file, fmt)
