import os
from oddasr.logic.odd_asr_file import OddAsrFile
from pynput import keyboard

asr = OddAsrFile()

def on_press(key):
    try:
        # 检测空格键
        if key == keyboard.Key.space:
            print("Space pressed. Starting recognition...")
            result = asr.transcribe_file("./test_cn_male_9s.wav")
            print(f"Recognition Result:\n{result}")
        # 检测退出键 'q'
        elif key.char == 'q':
            print("Quitting program.")
            return False
        else:
            print(f"Key pressed: {key.char}, but not recognized.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Press SPACE to recognize './test_cn_male_9s.wav', or 'q' to quit.")

    # 使用 pynput 监听按键
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()