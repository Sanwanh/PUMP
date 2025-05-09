#include <DFRobot_SIM7000.h>
#include <SoftwareSerial.h>
#include <Wire.h>
#include <avr/wdt.h>

// ======== Server Settings ========
#define SERVER_IP    "120.119.157.89"
#define SERVER_PORT  "7000"
#define API_PATH     "/api/simple-update"
#define DEVICE_ID    "A27"

// ======== Timing ========
unsigned long period   = 10000;  // 上傳間隔 (ms)
unsigned long time_now = 0;

// ======== Oil Level Sensor ========
const int ruptPin = 2;
int wt1 = 0;
int w1  = 0;

// ======== Emergency Switch ========
const int switchPin = 4;

// ======== NTC Sensor ========
const int analogPin = A0;
int hotsensor = 0;

// ======== Vibration Sensor ========
#define VIB_ADDR   (0x53)
#define VIB_BYTES  (6)
byte buff[VIB_BYTES];
int regAddress = 0x32;
int x, y, z;
int baselineX = 0;

// ======== Power Check ========
const int analogInput = A1;
float vin = 0.0;
const float R1 = 30000.0;
const float R2 = 7500.0;

// ======== Serial & SIM7000 ========
#define PIN_TX 7
#define PIN_RX 8
SoftwareSerial simSerial(PIN_RX, PIN_TX);
DFRobot_SIM7000 sim7000;

void setup() {
  Serial.begin(115200);
  simSerial.begin(19200);

  sim7000.begin(simSerial);
  sim7000.turnOFF(); delay(5000);
  Serial.println("Starting SIM7000...");
  if (!sim7000.turnON()) {
    Serial.println("Failed to power on SIM7000");
    return;
  }

  pinMode(switchPin, INPUT);
  pinMode(analogInput, INPUT);
  Wire.begin();

  writeTo(VIB_ADDR, 0x2D, 0);
  writeTo(VIB_ADDR, 0x2D, 16);
  writeTo(VIB_ADDR, 0x2D, 8);

  Serial.println("Setting baud rate...");
  if (!sim7000.setBaudRate(19200)) Serial.println("Failed to set baud rate");
  sim7000.initPos();

  simSerial.println("AT+CSTT=\"internet\""); delay(100);
  simSerial.println("AT+CSQ");              delay(100);
  simSerial.println("AT+CIPMUX=1");         delay(100);
  simSerial.println("AT+CIICR");            delay(100);
  simSerial.println("AT+CIFSR");            delay(100);

  readFrom(VIB_ADDR, regAddress, VIB_BYTES, buff);
  baselineX = ((int)buff[1] << 8) | buff[0];
  Serial.print("Baseline vibration X: "); Serial.println(baselineX);
}

void loop() {
  wdt_reset();

  readFrom(VIB_ADDR, regAddress, VIB_BYTES, buff);
  x = ((int)buff[1] << 8) | buff[0];
  y = ((int)buff[3] << 8) | buff[2];
  z = ((int)buff[5] << 8) | buff[4];
  Serial.print("Vibration X,Y,Z: "); Serial.print(x);
  Serial.print(", "); Serial.print(y);
  Serial.print(", "); Serial.println(z);

  powercheck();
  hot();
  water();

  int switchStatus = digitalRead(switchPin);
  int statusCode = 0;
  if (switchStatus == LOW) {
    statusCode = 4;
  } else {
    if (vin >= 11 && abs(baselineX - x) > 5 && hotsensor >= 40 && hotsensor <= 750) statusCode = 3;
    else if (vin >= 11 && abs(baselineX - x) > 5) statusCode = 2;
    else if (vin > 10) statusCode = 1;
    else statusCode = 0;
  }
  Serial.print("Oil OK: "); Serial.print(w1);
  Serial.print(" | Status: "); Serial.println(statusCode);

  bool gpsOK = (sim7000.getPosition() == 1);
  String latStr = gpsOK ? sim7000.getLatitude() : "1";
  String lonStr = gpsOK ? sim7000.getLongitude() : "1";

  // 組裝 URL
  String endpoint = String(API_PATH) + "?lon=" + lonStr
                    + "&lat="  + latStr
                    + "&s="    + String(statusCode)
                    + "&d="    + DEVICE_ID
                    + "&e="    + String(w1)
                    + "&f="    + String(vin, 2);

  // 列印完整 URL
  String fullUrl = String("http://") + SERVER_IP + ":" + SERVER_PORT + endpoint;
  Serial.print("Full URL: ");
  Serial.println(fullUrl);

  // 組裝 HTTP 請求
  String httpRequest = "GET " + endpoint + " HTTP/1.1\r\n"
                       "Host: " SERVER_IP ":" SERVER_PORT "\r\n"
                       "Connection: close\r\n\r\n";

  // 傳送請求
  Serial.println("Connecting to server...");
  simSerial.print("AT+CIPSTART=\"TCP\",\""); simSerial.print(SERVER_IP);
  simSerial.print("\", "); simSerial.println(SERVER_PORT);
  delay(200);

  simSerial.print("AT+CIPSEND="); simSerial.println(httpRequest.length());
  delay(200);
  simSerial.print(httpRequest);

  // 等待間隔
  time_now = millis();
  while (millis() - time_now < period) {}
}

void writeTo(int device, byte address, byte val) {
  Wire.beginTransmission(device);
  Wire.write(address);
  Wire.write(val);
  Wire.endTransmission();
}

void readFrom(int device, byte address, int num, byte buff[]) {
  Wire.beginTransmission(device);
  Wire.write(address);
  Wire.endTransmission();
  Wire.requestFrom(device, num);
  int i = 0;
  while (Wire.available() && i < num) buff[i++] = Wire.read();
}

void powercheck() {
  int value = analogRead(analogInput);
  float vout = (value * 5.0) / 1024.0;
  vin = vout / (R2 / (R1 + R2));
  Serial.print("Input Voltage: "); Serial.println(vin);
}

void hot() {
  hotsensor = analogRead(analogPin);
  Serial.print("NTC Sensor: "); Serial.println(hotsensor);
}

void water() {
  long sum = 0;
  for (int i = 0; i < 20; i++) { sum += analogRead(ruptPin); delay(5); }
  wt1 = sum / 20;
  w1 = (wt1 >= 1056) ? 1 : 0;
  Serial.print("Oil Level ADC: "); Serial.println(wt1);
}
