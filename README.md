###  ESP32-vocal-monitor

------

A lightweight IoT solution for voice-controlled motion detection using ESP32-CAM and ESP32. Combines real-time video analysis with voice commands.

Features:

- Chinese voice-activated camera control. (启动/关闭)
- Motion-triggered object detection by frame-difference.
- Multi-mode alerts (voice from controlling laptop, and beep from esp32c3).
- LAN operation.

------

### Hardware:

1. esp32-cam (For video fetching).
2. esp32c3 (For voice command detection and Beep notices).
3. An inmp441 microphone.
4. A passive buzzer.
5. A laptop as the core controller.

------

### Software:

1. [for esp32cam]: Just use the demo code of esp32-cam. A copy is included in esp32cam.cpp. You need to configure your Wifi information.

2. [for esp32c3]: esp32c3.cpp enable receiving voice signal from the microphone and controlling the buzzer to make beep notice. You need to configure parameters like the following:

   ```cpp
   // Pins, IP, and Wifi that you need to configure for your own environment.
   #define I2S_WS 5		// WS pin for INMP441
   #define I2S_SD 1		// SD pin for INMP441
   #define I2S_SCK 4		// SCK pin for INMP441
   						// for L/R pin in INMP441, just connect it to GND or VDD.
   #define BUZZER_PIN 0	// pin for BUZZER
   #define BUZZER_FREQ 2000
    
   const char* ssid = "Your 2.4g Wifi name.";
   const char* password = "Your 2.4g Wifi password";
   const char* host = "IP address of your laptop.";
   const int port = 8888;
   ```

3. [for laptop]: main.py use two threads to control 2 chips. It will open a cv2 window to show frames read from esp32-cam, and output some debug message to the terminal.

   ```python
   # -a parameter denotes the IP address of esp32c3
   parser.add_argument('-a', default='192.168.12.102', type=str, help='IP of esp32c3.')
   # -c parameter denotes the URL of esp32cam output
   parser.add_argument('-c', default='192.168.12.28', type=str, help='URL of esp32cam output address.')
   ```

4. [for Chinese vocal support]: Baidu API is used to detect and synthesize Chinese voice. Input your settings in baidu_voice.py and audio_detect.py.

   ```python
   APP_ID = ''
   API_KEY = ''
   SECRET_KEY = ''
   ```

------

### Operation:

1. Configure the settings in code and make sure the laptop and 2 chips are under the same LAN.
2. Burn corresponding .cpp code into esp32-cam and esp32c3. I believe there are lots of blogs on how to burn an esp32-cam.
3. Power on 2 chips. Press RST on esp32-cam. From the serial outputs, you can read the IP address of esp32c3 and esp32-cam output.
4. Run main.py with the above IP addresses.

------

This is a beginner's simple work. I'm expecting to see comments on how I can improve projects.