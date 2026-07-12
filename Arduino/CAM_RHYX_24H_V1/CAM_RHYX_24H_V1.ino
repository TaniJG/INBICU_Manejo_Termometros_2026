#include "esp_camera.h"
#include <WiFi.h>
#include "soc/soc.h"          // Para WRITE_PERI_REG
#include "soc/rtc_cntl_reg.h" // Para los registros de RTC
#include "driver/rtc_cntl.h"  // Necesario en versiones nuevas de ESP32 Core
#include "esp_sleep.h"        // Para deep sleep

// CONFIG
const char *ssid = "";
const char *password = "";
String serverName = ""; // Estos campo estan vacios, ya que utilizan datos sensibles
String serverPath = "/upload/";
const int serverPort = 8000;
String termometroID = ""; // El ID debe ser modificado de acuerdo al termometro al que se asignara la CAM

// Deep sleep configuration
#define SLEEP_DURATION_HOURS 8
#define SLEEP_DURATION_HOURS_FIRST_BOOT 8
#define uS_TO_S_FACTOR 1000000ULL // Conversion factor for micro seconds to seconds

// RTC memory variables (persist across deep sleep reboots)
RTC_DATA_ATTR int bootCount = 0;
RTC_DATA_ATTR bool firstBoot = true;

// AI Thinker ESP32-CAM pins (unchanged)
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22
#define FLASH_GPIO_NUM 4

WiFiClient client;

void setup()
{
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  Serial.begin(115200);
  delay(1000); // Allow serial to stabilize

  // Increment boot count
  bootCount++;
  Serial.println("\n\n=====================================");
  Serial.println("ESP32-CAM Daily Photo Capture");
  Serial.println("=====================================");
  Serial.println("Boot count: " + String(bootCount));

  // Check wake up reason
  esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();

  switch (wakeup_reason)
  {
  case ESP_SLEEP_WAKEUP_TIMER:
    Serial.println("Wakeup caused by timer (24h deep sleep)");
    break;
  case ESP_SLEEP_WAKEUP_UNDEFINED:
  default:
    Serial.println("Wakeup caused by reset or first boot");
    break;
  }

  // Flash
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  analogWrite(FLASH_GPIO_NUM, 0); // Asegurarse de que empiece apagado

  // WiFi
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);

  int wifiRetries = 0;
  while (WiFi.status() != WL_CONNECTED && wifiRetries < 30)
  {
    delay(500);
    Serial.print(".");
    wifiRetries++;
  }

  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("\nWiFi connection failed! Will retry in 24 hours.");
    goToDeepSleep();
    return; // Never reached but good practice
  }

  Serial.println("\nWiFi: " + WiFi.localIP().toString());

  // Camera (CIF for faster testing)
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000; // Baja freq estabilidad
  config.pixel_format = PIXFORMAT_RGB565;
  config.frame_size = FRAMESIZE_SVGA;
  config.jpeg_quality = 10;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_LATEST;

  if (esp_camera_init(&config) != ESP_OK)
  {
    Serial.println("Camera initialization failed! Will retry in 24 hours.");
    goToDeepSleep();
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  s->set_gain_ctrl(s, 0);     // DESACTIVADO el control automático de ganancia
  s->set_exposure_ctrl(s, 0); // DESACTIVADO el control automático de exposición
  s->set_agc_gain(s, 0);      // Ganancia manual al mínimo absoluto (0)
  s->set_brightness(s, -2);   // Brillo al mínimo (-2)
  s->set_contrast(s, 2);      // Contraste al máximo (2)
  s->set_saturation(s, -2);   // Escala de grises pura para el OCR
  s->set_whitebal(s, 0);      // Desactivar balance de blancos automático (fija los colores)
  s->set_bpc(s, 1);
  s->set_wpc(s, 1);
  s->set_aec_value(s, 15);

  // Go to deep sleep after completing work
  goToDeepSleep();
}

void loop()
{
  // Empty - everything happens in setup() because ESP32 restarts after deep sleep
  // This is never reached in normal operation
}

String sendPhoto()
{
  analogWrite(FLASH_GPIO_NUM, 5);
  delay(300);

  for (int i = 0; i < 5; i++)
  {
    camera_fb_t *fb_descarte = esp_camera_fb_get();
    if (fb_descarte)
    {
      esp_camera_fb_return(fb_descarte);
      delay(100);
    }
  }

  camera_fb_t *rgb_fb = esp_camera_fb_get();
  analogWrite(FLASH_GPIO_NUM, 0);
  if (!rgb_fb)
  {
    Serial.println("Capture failed");
    return "failed";
  }

  // Test 1: JPEG encode
  size_t jpg_len = 0;
  uint8_t *jpg_buf = NULL;
  bool encode_ok = frame2jpg(rgb_fb, 10, &jpg_buf, &jpg_len);
  esp_camera_fb_return(rgb_fb);

  Serial.printf("Encode %s - JPEG %.1fKB\n", encode_ok ? "OK" : "FAILED", jpg_len / 1024.0);

  // Upload si OK
  if (encode_ok && jpg_buf)
  {
    if (client.connect(serverName.c_str(), serverPort))
    {
      String head_id = "--DjangoBoundary\r\nContent-Disposition: form-data; name=\"id\"\r\n\r\n" + termometroID + "\r\n";
      String head_photo = "--DjangoBoundary\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"_rgb565.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n";
      String tail = "\r\n--DjangoBoundary--\r\n";

      uint32_t totalLen = head_id.length() + head_photo.length() + jpg_len + tail.length();

      client.print("POST " + serverPath + " HTTP/1.1\r\n");
      client.print("Host: " + serverName + "\r\n");
      client.print("Content-Length: " + String(totalLen) + "\r\n");
      client.print("Content-Type: multipart/form-data; boundary=DjangoBoundary\r\n");
      client.print("Connection: close\r\n\r\n");

      client.print(head_id);
      client.print(head_photo);

      uint8_t *buf = jpg_buf;
      size_t len = jpg_len;
      for (size_t i = 0; i < len; i += 1024)
      {
        client.write(buf, std::min((size_t)1024, len - i));
        buf += 1024;
      }

      client.print(tail);
      free(jpg_buf);

      String resp = "";
      unsigned long to = millis() + 5000;
      while (client.connected() && millis() < to)
      {
        while (client.available())
          resp += char(client.read());
      }
      client.stop();

      Serial.println("Django: " + resp);
      return resp;
    }
  }
  return "conn failed";
}

void goToDeepSleep()
{
  Serial.println("\nPreparing for deep sleep...");

  // Desconectarse del WiFi para horrar energia
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);

  // Des-inicializar la camara para horrar energia
  esp_camera_deinit();

  // Asegurarse que se apague el flash (flash nunca se prende, pero por las dudas)
  analogWrite(FLASH_GPIO_NUM, 0);

  // Flush serial output before sleep
  Serial.flush();

  // Define tiempo en el que duerme
  uint64_t sleepTimeMicroseconds;
  if (bootCount > 1)
  {
    sleepTimeMicroseconds = SLEEP_DURATION_HOURS * 3600ULL * uS_TO_S_FACTOR; // 180ULL * uS_TO_S_FACTOR; //
  }
  else
  {
    sleepTimeMicroseconds = SLEEP_DURATION_HOURS_FIRST_BOOT * 3600ULL * uS_TO_S_FACTOR; // 60ULL * uS_TO_S_FACTOR;; //
  }

  Serial.println("Entering deep sleep for " + String(SLEEP_DURATION_HOURS) + " hours...");
  Serial.println("Wake up in " + String(SLEEP_DURATION_HOURS) + " hours to take next photo");
  Serial.flush();

  esp_sleep_enable_timer_wakeup(sleepTimeMicroseconds);
  esp_deep_sleep_start();
}
