/**
 * 4G_A34.ino - 優化版本
 *
 * 此代碼用於帶有4G連接的多傳感器監控系統，包括：
 * - GPS定位
 * - 震動檢測
 * - 溫度監控 (NTC)
 * - 電源電壓監控
 * - 油位監控
 * - 緊急開關
 *
 * 數據通過SIM7000模組發送到遠程服務器
 */

#include <DFRobot_SIM7000.h>
#include <SoftwareSerial.h>
#include <Wire.h>
#include <avr/wdt.h>

// ===== 常量定義 =====
#define PIN_TX 7         // SIM7000模組TX接腳
#define PIN_RX 8         // SIM7000模組RX接腳
#define DEVICE_ADDR 0x53 // 震動感測器I2C位址
#define REG_ADDR 0x32    // 震動感測器數據寄存器
#define DATA_LEN 6       // 震動感測器數據長度

#define SERVER_IP "120.119.155.138" // 伺服器IP
#define SERVER_PORT 7000            // 伺服器埠 - 改為7000以匹配main.py中的端口
#define DEVICE_ID "A27"             // 裝置ID

#define POWER_THRESHOLD_LOW 10.0    // 低電量閾值
#define POWER_THRESHOLD_NORMAL 11.0 // 正常電量閾值
#define MOTION_THRESHOLD 5          // 震動檢測閾值
#define TEMP_MIN 40                 // 最低溫度閾值
#define TEMP_MAX 750                // 最高溫度閾值
#define OIL_THRESHOLD 1055          // 油位閾值
#define DATA_SEND_INTERVAL 10000    // 數據發送間隔(毫秒)
#define WDT_RESET_COUNT 1000        // Watchdog重置計數閾值

// ===== 引腳定義 =====
const int PIN_EMERGENCY = 4; // 緊急開關引腳
const int PIN_OIL_LEVEL = 2; // 油位傳感器引腳
const int PIN_NTC = A0;      // 溫度傳感器引腳
const int PIN_VOLTAGE = A1;  // 電壓檢測引腳

// ===== 全域變數 =====
// 系統狀態
unsigned long lastSendTime = 0; // 上次數據發送時間
int resetCounter = 0;           // 重啟計數器
int systemStatus = 0;           // 系統狀態碼

// 傳感器相關
int initialAccelX = 0;      // 初始X軸加速度值
byte accelBuffer[DATA_LEN]; // 加速度感測器緩衝區
int accelX, accelY, accelZ; // 加速度值
int oilLevel = 0;           // 油位狀態 (0=低, 1=高)
int oilReading = 0;         // 油位讀數
int tempReading = 0;        // 溫度讀數
float voltage = 0.0;        // 電壓值

// 電壓檢測相關
const float R1 = 30000.0; // 電壓檢測電阻1 (歐姆)
const float R2 = 7500.0;  // 電壓檢測電阻2 (歐姆)

// SIM7000相關
SoftwareSerial sim7000Serial(PIN_RX, PIN_TX); // SIM7000串口
DFRobot_SIM7000 sim7000;                      // SIM7000物件

/**
 * 初始化函數
 */
void setup()
{
  // 初始化串口
  Serial.begin(115200);
  Serial.println(F("===== 系統啟動 ====="));

  // 初始化引腳
  pinMode(PIN_EMERGENCY, INPUT);
  pinMode(PIN_VOLTAGE, INPUT);
  pinMode(PIN_NTC, INPUT);

  // 初始化I2C通訊
  Wire.begin();

  // 初始化震動傳感器
  initAccelerometer();

  // 初始化並保存基準加速度值
  readAccelerometer();
  initialAccelX = accelX;
  Serial.print(F("初始加速度X值: "));
  Serial.println(initialAccelX);

  // 初始化SIM7000模組
  if (!initSIM7000())
  {
    Serial.println(F("SIM7000初始化失敗!"));
    systemReset(); // 重啟系統
  }

  // 啟用看門狗計時器，8秒超時
  wdt_enable(WDTO_8S);

  Serial.println(F("===== 初始化完成 ====="));
}

/**
 * 主循環函數
 */
void loop()
{
  // 重置看門狗計時器
  wdt_reset();

  // 計數器管理
  resetCounter++;
  if (resetCounter >= WDT_RESET_COUNT)
  {
    resetCounter = 0;
    // 短時看門狗重啟系統
    systemReset();
  }

  // 讀取所有傳感器數據
  readSensors();

  // 更新系統狀態
  updateSystemStatus();

  // 發送數據
  if (millis() - lastSendTime >= DATA_SEND_INTERVAL)
  {
    sendDataToServer();
    lastSendTime = millis();
  }
}

/**
 * 初始化SIM7000模組
 */
bool initSIM7000()
{
  // 關閉模組後重新啟動
  sim7000.begin(sim7000Serial);
  sim7000.turnOFF();
  delay(5000);

  Serial.println(F("啟動SIM7000..."));
  if (!sim7000.turnON())
  {
    Serial.println(F("啟動SIM7000失敗!"));
    return false;
  }
  Serial.println(F("SIM7000啟動成功!"));

  // 設置波特率
  if (!sim7000.setBaudRate(19200))
  {
    Serial.println(F("設置波特率失敗!"));
    return false;
  }
  Serial.println(F("波特率設置為19200"));

  // 初始化定位功能
  if (!sim7000.initPos())
  {
    Serial.println(F("定位功能初始化失敗!"));
    return false;
  }
  Serial.println(F("定位功能初始化成功!"));

  // 配置網路連接
  sim7000Serial.begin(19200);
  sendATCommand("AT+CGNAPN");
  sendATCommand("AT+CSTT=internet"); // 使用internet APN
  sendATCommand("AT+CSQ");
  sendATCommand("AT+CIPMUX=1");
  sendATCommand("AT+CIICR");
  sendATCommand("AT+CIFSR");

  return true;
}

/**
 * 發送AT命令到SIM7000
 */
void sendATCommand(const char *command)
{
  sim7000Serial.println(command);
  delay(100);
}

/**
 * 初始化加速度計
 */
void initAccelerometer()
{
  // 初始化加速度感測器
  writeToAccelerometer(0x2D, 0);
  writeToAccelerometer(0x2D, 16);
  writeToAccelerometer(0x2D, 8);
}

/**
 * 寫入加速度計寄存器
 */
void writeToAccelerometer(byte address, byte value)
{
  Wire.beginTransmission(DEVICE_ADDR);
  Wire.write(address);
  Wire.write(value);
  Wire.endTransmission();
}

/**
 * 讀取加速度計數據
 */
void readAccelerometer()
{
  Wire.beginTransmission(DEVICE_ADDR);
  Wire.write(REG_ADDR);
  Wire.endTransmission();

  Wire.beginTransmission(DEVICE_ADDR);
  Wire.requestFrom(DEVICE_ADDR, DATA_LEN);

  int i = 0;
  while (Wire.available() && i < DATA_LEN)
  {
    accelBuffer[i] = Wire.read();
    i++;
  }
  Wire.endTransmission();

  // 計算加速度值
  accelX = (((int)accelBuffer[1]) << 8) | accelBuffer[0];
  accelY = (((int)accelBuffer[3]) << 8) | accelBuffer[2];
  accelZ = (((int)accelBuffer[5]) << 8) | accelBuffer[4];
}

/**
 * 讀取所有傳感器數據
 */
void readSensors()
{
  // 讀取加速度
  readAccelerometer();

  // 讀取電壓
  readVoltage();

  // 讀取溫度
  readTemperature();

  // 讀取油位
  readOilLevel();

  // 顯示傳感器數據
  printSensorData();
}

/**
 * 讀取電壓
 */
void readVoltage()
{
  int value = analogRead(PIN_VOLTAGE);
  float vout = (value * 5.0) / 1024.0;
  voltage = vout / (R2 / (R1 + R2));
}

/**
 * 讀取溫度
 */
void readTemperature()
{
  tempReading = analogRead(PIN_NTC);
}

/**
 * 讀取油位
 */
void readOilLevel()
{
  // 取20次讀數平均值
  int totalReading = 0;
  for (int i = 0; i < 20; i++)
  {
    totalReading += analogRead(PIN_OIL_LEVEL);
  }
  oilReading = totalReading / 20;

  // 根據閾值更新油位狀態
  oilLevel = (oilReading >= OIL_THRESHOLD) ? 1 : 0;
}

/**
 * 輸出傳感器數據
 */
void printSensorData()
{
  Serial.println(F("--------- 傳感器數據 ---------"));

  Serial.print(F("加速度: X="));
  Serial.print(accelX);
  Serial.print(F(" Y="));
  Serial.print(accelY);
  Serial.print(F(" Z="));
  Serial.println(accelZ);

  Serial.print(F("電壓: "));
  Serial.println(voltage);

  Serial.print(F("溫度讀數: "));
  Serial.println(tempReading);

  Serial.print(F("油位讀數: "));
  Serial.print(oilReading);
  Serial.print(F(" 狀態: "));
  Serial.println(oilLevel);

  Serial.print(F("緊急開關: "));
  Serial.println(digitalRead(PIN_EMERGENCY));

  Serial.print(F("系統狀態: "));
  Serial.println(systemStatus);

  Serial.println(F("-------------------------------"));
}

/**
 * 更新系統狀態代碼
 */
void updateSystemStatus()
{
  // 讀取緊急開關狀態
  int emergencySwitch = digitalRead(PIN_EMERGENCY);

  // 判斷系統狀態
  if (emergencySwitch == LOW)
  {
    // 緊急狀態
    systemStatus = 4;
  }
  else
  {
    if (voltage >= POWER_THRESHOLD_NORMAL)
    {
      // 電壓正常
      int accelerationDelta = abs(initialAccelX - accelX);

      if (accelerationDelta > MOTION_THRESHOLD)
      {
        // 檢測到震動
        if (tempReading <= TEMP_MAX && tempReading >= TEMP_MIN)
        {
          // 溫度正常 + 震動 + 電壓正常
          systemStatus = 3;
        }
        else
        {
          // 溫度異常 + 震動 + 電壓正常
          systemStatus = 2;
        }
      }
      else
      {
        // 無震動 + 電壓正常
        systemStatus = 1;
      }
    }
    else if (voltage <= POWER_THRESHOLD_LOW)
    {
      // 電壓低
      systemStatus = 0;
    }
  }
}

/**
 * 發送數據到伺服器
 */
void sendDataToServer()
{
  // 獲取GPS位置
  String latitude = "1";
  String longitude = "1";

  bool gpsValid = false;

  // 嘗試獲取GPS位置
  if (sim7000.getPosition())
  {
    latitude = sim7000.getLatitude();
    longitude = sim7000.getLongitude();
    gpsValid = true;
    Serial.println(F("GPS位置獲取成功"));
  }
  else
  {
    Serial.println(F("GPS位置獲取失敗，使用默認值"));
  }

  // 構建HTTP GET請求，使用/api/simple-update端點
  // 參數格式: /api/simple-update?lon=經度&lat=緯度&s=狀態碼&d=裝置ID&e=油位&f=其他數值
  String cmd = "GET /api/simple-update";
  cmd += "?lon=" + longitude;
  cmd += "&lat=" + latitude;
  cmd += "&s=" + String(systemStatus);
  cmd += "&d=" + String(DEVICE_ID);
  cmd += "&e=" + String(oilLevel);
  cmd += "&f=" + String(voltage, 2);
  cmd += " HTTP/1.1\r\nHost: " + String(SERVER_IP) + "\r\n\r\n";

  // 建立TCP連接
  sendATCommand(("AT+CIPSTART=\"TCP\",\"" + String(SERVER_IP) + "\"," + String(SERVER_PORT)).c_str());

  // 發送數據
  sim7000Serial.print("AT+CIPSEND=");
  sim7000Serial.println(cmd.length());
  delay(100);
  sim7000Serial.println(cmd);

  Serial.print(F("已發送數據: "));
  Serial.println(cmd);

  // 等待數據發送完成
  Serial.println(F("等待下一個發送週期..."));
}

/**
 * 系統重置
 */
void systemReset()
{
  Serial.println(F("系統即將重置..."));
  wdt_enable(WDTO_15MS); // 設置15ms超時 - 強制重啟
  while (1)
  {
  } // 等待WDT重啟系統
}

/**
 * 讀取串口數據 (未使用，保留以備後用)
 */
int readSerial(char result[])
{
  int i = 0;
  if (Serial.available() > 0)
  {
    char inChar = Serial.read();
    if (inChar == '\n')
    {
      result[i] = '\0';
      Serial.flush();
      return 0;
    }
    if (inChar != '\r')
    {
      result[i] = inChar;
      i++;
    }
  }
  return 1;
}