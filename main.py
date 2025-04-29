# define PY_SSIZE_T_CLEAN
import cv2
from yolo_detect import Detector
from baidu_voice import Speaker
import pyaudio
import socket
import wave
import time
from datetime import datetime
from audio_detect import detect_file
import threading
import argparse
import numpy as np

# esp32audio config
CHUNK = 2048
SAMPLE_RATE = 16000
FORMAT = pyaudio.paInt16
CHANNELS = 1
UDP_PORT = 8888
RECORD_SECONDS = 5

parser = argparse.ArgumentParser(description="esp32c3 & esp32cam ip control")


def save_audio_to_file(frames, filename):
    """将音频帧保存为WAV文件"""
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


def generate_filename():
    """生成带时间戳的文件名"""
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    # return f"audio_{now}.wav"
    return f"audio_0.wav"


last_beep_time = -10
beep_interval = 3
def send_beep_signal(esp32_ip, port=8888):
    global last_beep_time, beep_interval
    if time.time()-last_beep_time < beep_interval:
        return
    last_beep_time = time.time()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b'BEEP', (esp32_ip, port))
    sock.close()
    print("BEEP 信号已发送至 ESP32")


MOTION_THRESHOLD = 140


# def move_detection(frame_0, frame_1):
#     """
#     detect movement by the difference between two near frames
#     :param frame_0: older frame
#     :param frame_1: new frame
#     :return: 1/0
#     """
#     e = (frame_1-frame_0).sum()/frame_1.size
#     # print(f'this difference per pixel: {e}')
#     if e>MOTION_THRESHOLD:
#         return True
#     else:
#         return False


def move_detection(frame_0, frame_1, threshold=25, min_contour_area=500):
    """
    标准帧差法移动检测（带噪声处理和区域过滤）

    参数:
        frame_0: 灰度化的前一帧 (numpy.ndarray)
        frame_1: 灰度化的当前帧 (numpy.ndarray)
        threshold: 二值化阈值 (默认25)
        min_contour_area: 有效移动区域最小面积 (默认500像素)

    返回:
        bool: 是否检测到有效移动
        numpy.ndarray: 可视化结果帧 (可选)
    """
    if len(frame_0.shape) == 3:
        frame_0 = cv2.cvtColor(frame_0, cv2.COLOR_BGR2GRAY)
    if len(frame_1.shape) == 3:
        frame_1 = cv2.cvtColor(frame_1, cv2.COLOR_BGR2GRAY)

    frame_0_blur = cv2.GaussianBlur(frame_0, (5, 5), 0)
    frame_1_blur = cv2.GaussianBlur(frame_1, (5, 5), 0)

    delta = cv2.absdiff(frame_0_blur, frame_1_blur)

    thresh = cv2.threshold(delta, threshold, 255, cv2.THRESH_BINARY)[1]

    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=2)
    thresh = cv2.erode(thresh, kernel, iterations=1)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    for cnt in contours:
        if cv2.contourArea(cnt) > min_contour_area:
            motion_detected = True
            break

    debug_frame = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    for cnt in contours:
        if cv2.contourArea(cnt) > min_contour_area:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # return motion_detected, debug_frame
    return motion_detected



def voice_notice(speaker, name, number):
    """
    Use Baidu Api to generate human voice notification for the object detection result(prompt)
    :param prompt: name and number of the detected object
    :return: nothing
    """
    print(f'input:{name}, {number}')
    translate_dict = {
        "person" : "人",
        "tv" : "电视",
        "desk" : "桌板",
        "chair" : "椅子",
        "table" : "桌子",
        "laptop" : "电脑"
    }
    text = "产生移动，"
    if name is not None and number is not None:
        if name in translate_dict:
            text += f"检测到{number}个{translate_dict[name]}"
        else:
            text += f"检测到{number}个物体"
    speaker.speak_text(text)


# ------------Threading Control Signals------------
FINISH = False
CAMERA_ON = True
CURRENT_FRAME = None
# -------------------------------------------------


def esp32cam_control(camera_url, esp32_ip):
    global FINISH, CAMERA_ON, CURRENT_FRAME

    # url = input("# input IP of esp32 streaming:")
    # url = '192.168.2.103'
    esp32_url = f'http://{camera_url}:81/stream'
    cap = cv2.VideoCapture(esp32_url)

    object_detection_flag = True
    detector = Detector()

    voice_notice_flag = True
    speaker = Speaker()
    speak_interval = 6  # seconds
    last_speak_time = -speak_interval

    if not cap.isOpened():
        print("[ERROR](cam thread): Cannot capture video.")
        FINISH = True
        return

    last_frame = None
    while not FINISH:
        # wait until camera on
        while not CAMERA_ON:
            time.sleep(0.1)
            ret, frame = cap.read()

        ret, frame = cap.read()
        CURRENT_FRAME = frame
        if not ret:
            print("[ERROR](cam thread): Cannot read frame.")
            FINISH = True
            break
        if last_frame is None:
            last_frame = frame

        if move_detection(last_frame, frame):
            print(f'Motion Detected!')
            send_beep_signal(esp32_ip)  # emit alarming signal
            if object_detection_flag:
                detect_res = detector(frame)
                print(f'detected:{detect_res}')
                if voice_notice_flag and time.time()-last_speak_time>speak_interval:
                    last_speak_time = time.time()
                    if detect_res is not None:
                        voice_notice(speaker, detect_res[-1][0], detect_res[-1][1])
                    else:
                        voice_notice(speaker, None, None)
        last_frame = frame

    cap.release()


def esp32audio_control():
    global p, CAMERA_ON, CURRENT_FRAME, FINISH

    p = pyaudio.PyAudio()

    # audio stream on
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True)

    # UDP socket on
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65535)

    print(f"[DEBUG](audio thread): Start receiving UDP audio (port {UDP_PORT})...")

    frames = []
    one_full = False
    while not FINISH:
        temp_frames = []
        start_time = time.time()

        # recording audio of specific length
        while (time.time() - start_time) < RECORD_SECONDS:
            data, _ = sock.recvfrom(CHUNK)
            frames.append(data)
            temp_frames.append(data)
            # stream.write(data)
        if not one_full:
            one_full = True
        else:
            filename = generate_filename()
            save_audio_to_file(frames, filename)
            detection = detect_file(filename)
            if detection == 1:
                CAMERA_ON = True
            elif detection == 0:
                CAMERA_ON = False
            # thread = threading.Thread(target=detect_file, args=(filename, send_beep_signal))
            # thread.start()
            frames = temp_frames

    stream.stop_stream()
    stream.close()
    sock.close()
    p.terminate()


def core_control():
    global FINISH, CAMERA_ON, CURRENT_FRAME

    while not FINISH:
        if CURRENT_FRAME is not None:
            frame = CURRENT_FRAME.copy()
            cv2.imshow("ESP32-CAM", frame)
        else:
            print(f'[DEBUG](main thread):CURRENT_FRAME is None')

        # press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            FINISH = True
            break

    cv2.destroyAllWindows()


def main():
    parser.add_argument('-a', default='192.168.12.102', type=str, help='IP of esp32c3.')
    parser.add_argument('-c', default='192.168.12.28', type=str, help='URL of esp32cam output address.')
    args = parser.parse_args()
    global FINISH, CAMERA_ON, CURRENT_FRAME
    
    # threading on
    thread_cam = threading.Thread(target=esp32cam_control, args=(args.c, args.a))
    thread_audio = threading.Thread(target=esp32audio_control)
    thread_core = threading.Thread(target=core_control)
    thread_cam.start()
    thread_audio.start()
    thread_core.start()


if __name__=="__main__":
    main()