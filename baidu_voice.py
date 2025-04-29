import re
import simpleaudio
from xpinyin import Pinyin
import threading
import os
import pyaudio
import wave
from aip import AipSpeech
from pydub import AudioSegment, playback


APP_ID = ''
API_KEY = ''
SECRET_KEY = ''

# client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
WAVE_OUTPUT_FILENAME = "audio.wav"

def record():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 8000
    RECORD_SECONDS = 3

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    stream.start_stream()
    print("Start recording...")

    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()

    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as file:
        file.setnchannels(CHANNELS)
        file.setsampwidth(p.get_sample_size(FORMAT))
        file.setframerate(RATE)
        file.writeframes(b''.join(frames))


def get_text(filename):
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

    with open(filename, 'rb') as file:
        wave = file.read()

    print(f"* recognizing {len(wave)}")
    result = client.asr(wave, 'wav',16000, {'dev_pid':1537})
    print(result)
    if result["err_no"] == 0:
        return result['result'][0]
    else:
        # print(f"Fail to recognize. {result['err_no']}")
        return None


class Speaker:
    def __init__(self, filename = 'speech.mp3'):
        self.client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
        # self.py = Pinyin()
        self.audio_path = os.path.abspath(filename)
        self.speak_obj = None

    def speak_text(self, text):
        voice = self.client.synthesis(text, 'zh', 6, {'vol': 10, 'per': 3, 'spd': 5})
        with open(self.audio_path, 'wb') as file:
            file.write(voice)
        self.speak_obj = AudioSegment.from_mp3(self.audio_path)
        self.speak_audio()

    def speak_audio(self):
        if self.speak_obj is None:
            if os.path.exists(self.audio_path):
                self.speak_obj = AudioSegment.from_mp3(self.audio_path)
            else:
                print('Nothing to speak!')
                return
        playback.play(self.speak_obj)
        # t = threading.Thread(target=play_sa_obj, args=(self.speak_obj, ))
        # t.start()


def play_sa_obj(obj):
    play_obj = obj.play()
    play_obj.wait_done()


def main():
    pass


if __name__=="__main__":
    main()
