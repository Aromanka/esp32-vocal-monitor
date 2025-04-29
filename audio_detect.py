import re
from xpinyin import Pinyin
from aip import AipSpeech
from baidu_voice import Speaker

APP_ID = ''
API_KEY = ''
SECRET_KEY = ''


client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
camera_on_audio = Speaker('camera.mp3')
# WAVE_OUTPUT_FILENAME = "audio.wav"


def get_text(filename):
    with open(filename, 'rb') as file:
        wave = file.read()

    result = client.asr(wave, 'wav',16000, {'dev_pid':1537})
    if result["err_no"] == 0:
        return result['result'][0]
    else:
        return None


def detect_pinyin(text):
    PY = Pinyin()
    py = PY.get_pinyin(text)

    pt_1 = r"qi-dong"
    pt_2 = r"guan-bi"


    if re.search(pt_1, py):
        print('monitor activate')
        camera_on_audio.speak_text("摄像头开始工作")
        return 1
    elif re.search(pt_2, py):
        print('monitor deactivate')
        camera_on_audio.speak_text("摄像头停止工作")
        return 0
    else:
        return -1


def detect_file(filename):
    """
    detect the qidong/guanbi in the given audio file
    :param filename: target audio file
    :return: 1 if qidong/ 0 if guanbi/ -1 if none
    """
    text = get_text(filename)
    if text is not None:
        return detect_pinyin(text)
    else:
        return None
