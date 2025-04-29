#define USE_ESP32_WIFI_LIB
#include <Arduino.h>
#include <driver/i2s.h>
#include <WiFiUdp.h>
#include <WiFi.h>
 
#define I2S_WS 5
#define I2S_SD 1
#define I2S_SCK 4
#define BUZZER_PIN 0
#define BUZZER_FREQ 2000
#define I2S_PORT I2S_NUM_0
#define bufferLen 1024
 
const char* ssid = "";
const char* password = "";
const char* host = "";
const int port = 8888;
 
WiFiUDP udp;
int16_t sBuffer[bufferLen];
 
void setup() {
    Serial.begin(115200);
    Serial.println("Setup I2S ...");
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(600);
        Serial.print("-");
    }
    Serial.println("WiFi 已连接");
    Serial.println("IP 地址: ");
    Serial.println(WiFi.localIP());
    
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = 16000,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = (i2s_comm_format_t)(I2S_COMM_FORMAT_STAND_I2S),
        .intr_alloc_flags = 0,
        .dma_buf_count = 8,
        .dma_buf_len = bufferLen,
        .use_apll = false
    };
    i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD
    };
    i2s_set_pin(I2S_PORT, &pin_config);
    i2s_start(I2S_PORT);
    
    // BUZZER
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW); // 默认不响
    ledcSetup(0, BUZZER_FREQ, 8); // 设置PWM通道0，频率，分辨率8位
    ledcAttachPin(BUZZER_PIN, 0); // 将PWM通道0附加到蜂鸣器引脚
    udp.begin(port); // 开启 UDP 监听
}
 
void loop() {
    size_t bytesIn = 0;
    esp_err_t result = i2s_read(I2S_PORT, &sBuffer, bufferLen * sizeof(int16_t), &bytesIn, portMAX_DELAY);
    if (result == ESP_OK && bytesIn > 0) {
        udp.beginPacket(host, port);
        udp.write((uint8_t*)sBuffer, bytesIn);
        udp.endPacket();
    }
    
    // BUZZER
    int packetSize = udp.parsePacket();
    if (packetSize > 0) {
        char incoming[16];
        int len = udp.read(incoming, sizeof(incoming) - 1);
        if (len > 0) {
            incoming[len] = 0;
            if (strcmp(incoming, "BEEP") == 0) {
                // beep 200ms
                ledcWriteTone(0, BUZZER_FREQ);
                delay(200);
                ledcWrite(0, 0);
            }
        }
    }
}