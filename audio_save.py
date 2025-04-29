# define PY_SSIZE_T_CLEAN
import pyaudio
import socket
import wave
import time
from datetime import datetime
from audio_detect import detect_file
import threading

# configure
esp32_ip = "192.168.12.102"
CHUNK = 2048
SAMPLE_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
UDP_PORT = 8888
RECORD_SECONDS = 2.5


def save_audio_to_file(frames, filename):
    """将音频帧保存为WAV文件"""
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"音频已保存为 {filename}")


def generate_filename():
    """生成带时间戳的文件名"""
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    # return f"audio_{now}.wav"
    return f"audio_0.wav"


def send_beep_signal(port=8888):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b'BEEP', (esp32_ip, port))
    sock.close()
    print("BEEP 信号已发送至 ESP32")


def main():
    global p

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65535)

    print(f"开始接收UDP音频（端口 {UDP_PORT}）...")
    print("按Ctrl+C停止录制")

    try:
        frames = []
        one_full = False
        while True:
            temp_frames = []
            start_time = time.time()

            while (time.time() - start_time) < RECORD_SECONDS:
                data, _ = sock.recvfrom(CHUNK)
                frames.append(data)
                temp_frames.append(data)
                stream.write(data)
            if not one_full:
                one_full = True
            else:
                filename = generate_filename()
                save_audio_to_file(frames, filename)
                thread = threading.Thread(target=detect_file, args=(filename, send_beep_signal))
                thread.start()
                frames = temp_frames

    except KeyboardInterrupt:
        print("\n录制停止")
    finally:
        stream.stop_stream()
        stream.close()
        sock.close()
        p.terminate()


if __name__ == "__main__":
    main()