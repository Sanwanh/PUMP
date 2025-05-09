# 設備監控系統程式碼解析

## 概述

本文檔詳細解析了一個基於 Arduino 平台的設備監控系統。該系統使用 SIM7000 通訊模組連接網路，並整合了多種感測器來監測設備的運行狀態，包括油位、溫度、振動和電源狀態等。系統會定期將收集到的數據透過 HTTP 請求傳送到指定的伺服器進行集中管理。

## 系統架構

### 硬體組成

- **主控制器**：Arduino (AVR 架構)
- **通訊模組**：SIM7000 (提供行動網路連接和 GPS 功能)
- **感測器**：
  - 油位感測器（連接到數位針腳 2）
  - NTC 溫度感測器（連接到類比針腳 A0）
  - 振動感測器（I2C 介面，地址 0x53）
  - 電壓監測（連接到類比針腳 A1，通過分壓電路）
  - 緊急開關（連接到數位針腳 4）

### 軟體架構

程式碼主要分為以下幾個功能模塊：
1. 初始化設置（`setup()` 函數）
2. 主循環（`loop()` 函數）
3. 感測器資料採集處理（各個專用函數）
4. 網路通訊（HTTP 請求構建與發送）

## 功能詳解

### 1. 系統參數設置

```c
// 伺服器設置
#define SERVER_IP    "120.119.157.89"
#define SERVER_PORT  "7000"
#define API_PATH     "/api/simple-update"
#define DEVICE_ID    "A27"

// 時間設置
unsigned long period   = 10000;  // 上傳間隔 (ms)
```

這部分定義了系統的基本參數，包括目標伺服器的 IP 地址和端口、API 端點路徑、設備唯一標識符，以及數據上傳的時間間隔（10 秒）。

### 2. 感測器初始化與配置

系統在 `setup()` 函數中完成所有感測器和通訊模組的初始化：

```c
void setup() {
  Serial.begin(115200);
  simSerial.begin(19200);

  // SIM7000 模組初始化
  sim7000.begin(simSerial);
  sim7000.turnOFF(); delay(5000);
  sim7000.turnON();
  
  // 針腳設置
  pinMode(switchPin, INPUT);
  pinMode(analogInput, INPUT);
  
  // I2C 設置 (振動感測器)
  Wire.begin();
  writeTo(VIB_ADDR, 0x2D, 0);
  writeTo(VIB_ADDR, 0x2D, 16);
  writeTo(VIB_ADDR, 0x2D, 8);
  
  // 設置 SIM7000 和網路連接
  sim7000.setBaudRate(19200);
  sim7000.initPos();
  simSerial.println("AT+CSTT=\"internet\"");
  // ...其他 AT 指令...
  
  // 獲取振動基準值
  readFrom(VIB_ADDR, regAddress, VIB_BYTES, buff);
  baselineX = ((int)buff[1] << 8) | buff[0];
}
```

### 3. 數據採集與處理

系統會在每次循環中採集所有感測器的數據：

#### 振動感測器

```c
readFrom(VIB_ADDR, regAddress, VIB_BYTES, buff);
x = ((int)buff[1] << 8) | buff[0];
y = ((int)buff[3] << 8) | buff[2];
z = ((int)buff[5] << 8) | buff[4];
```

通過 I2C 協議讀取振動感測器的三軸加速度數據，並將高位元組和低位元組合併為 16 位整數值。

#### 電源電壓監測

```c
void powercheck() {
  int value = analogRead(analogInput);
  float vout = (value * 5.0) / 1024.0;
  vin = vout / (R2 / (R1 + R2));
}
```

採用電阻分壓原理測量輸入電壓。通過已知的分壓比例（R1=30000Ω，R2=7500Ω）計算實際電壓值。

#### 溫度監測

```c
void hot() {
  hotsensor = analogRead(analogPin);
}
```

直接讀取 NTC 溫度感測器的類比值。

#### 油位監測

```c
void water() {
  long sum = 0;
  for (int i = 0; i < 20; i++) { sum += analogRead(ruptPin); delay(5); }
  wt1 = sum / 20;
  w1 = (wt1 >= 1056) ? 1 : 0;
}
```

通過多次採樣並取平均值來提高油位感測器的讀數準確性。當讀數超過閾值 1056 時，視為油位正常（設置 w1 為 1）。

### 4. 狀態判斷邏輯

系統根據多個感測器的數據綜合判斷設備的運行狀態：

```c
int statusCode = 0;
if (switchStatus == LOW) {
  statusCode = 4;
} else {
  if (vin >= 11 && abs(baselineX - x) > 5 && hotsensor >= 40 && hotsensor <= 750) statusCode = 3;
  else if (vin >= 11 && abs(baselineX - x) > 5) statusCode = 2;
  else if (vin > 10) statusCode = 1;
  else statusCode = 0;
}
```

狀態碼含義：
- **狀態碼 0**：電源電壓低於 10V（可能斷電或電池電量不足）
- **狀態碼 1**：電源電壓正常（大於 10V）
- **狀態碼 2**：電源正常且有振動（振動值與基準線差異大於 5）
- **狀態碼 3**：電源正常、振動正常、溫度在正常範圍內（40-750）
- **狀態碼 4**：緊急開關被觸發（開關為 LOW 狀態）

### 5. GPS 位置獲取

```c
bool gpsOK = (sim7000.getPosition() == 1);
String latStr = gpsOK ? sim7000.getLatitude() : "1";
String lonStr = gpsOK ? sim7000.getLongitude() : "1";
```

嘗試通過 SIM7000 模組獲取當前的 GPS 位置。如果成功，則使用實際的經緯度；如果失敗，則使用預設值 "1"。

### 6. 數據上傳

系統組裝 HTTP GET 請求，並通過 SIM7000 模組發送到指定的伺服器：

```c
// 組裝 URL
String endpoint = String(API_PATH) + "?lon=" + lonStr
                  + "&lat="  + latStr
                  + "&s="    + String(statusCode)
                  + "&d="    + DEVICE_ID
                  + "&e="    + String(w1)
                  + "&f="    + String(vin, 2);

// 組裝 HTTP 請求
String httpRequest = "GET " + endpoint + " HTTP/1.1\r\n"
                     "Host: " SERVER_IP ":" SERVER_PORT "\r\n"
                     "Connection: close\r\n\r\n";

// 傳送請求
simSerial.print("AT+CIPSTART=\"TCP\",\""); simSerial.print(SERVER_IP);
simSerial.print("\", "); simSerial.println(SERVER_PORT);
delay(200);

simSerial.print("AT+CIPSEND="); simSerial.println(httpRequest.length());
delay(200);
simSerial.print(httpRequest);
```

上傳的數據參數包括：
- `lon`：經度
- `lat`：緯度
- `s`：設備狀態碼 (0-4)
- `d`：設備 ID (固定為 "A27")
- `e`：油位狀態 (0 或 1)
- `f`：電源電壓值

### 7. 定時執行

```c
// 等待間隔
time_now = millis();
while (millis() - time_now < period) {}
```

系統使用 `millis()` 函數實現非阻塞延時，每 10 秒執行一次完整的監測和上傳循環。

### 8. 安全措施

```c
wdt_reset();
```

在每個循環開始時重置看門狗定時器 (WDT)，防止程式卡死導致系統無響應。

## I2C 通訊輔助函數

```c
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
```

這兩個函數封裝了 I2C 通訊的讀寫操作，用於與振動感測器進行通訊。

## 應用場景

該監控系統適用於需要遠程監控的設備，特別是：

1. **工業設備監控**：監測發電機、引擎或工業機械的運行狀態
2. **遠端基礎設施**：監控分散在各地的基礎設施設備
3. **無人值守設備**：需要定期檢查但人員不便常駐的設備

## 系統優勢

1. **多參數監測**：同時監測多個關鍵參數（溫度、振動、電源、油位）
2. **遠程連接**：通過移動網路實現遠程數據傳輸，不受區域網路限制
3. **位置追蹤**：集成 GPS 功能，可追蹤設備位置
4. **綜合狀態判斷**：通過多個參數的組合分析判斷設備狀態
5. **定期上報**：自動定期將數據上傳到中央伺服器
6. **可靠性設計**：使用看門狗機制確保系統穩定運行

## 結論

這套設備監控系統是一個集感測器數據採集、狀態判斷、網路通訊於一體的完整解決方案。它能夠有效地監測設備的運行狀態，並將數據實時傳輸到中央伺服器，為設備管理和維護提供了有力的技術支持。

系統採用 Arduino 平台和 SIM7000 通訊模組，結構簡單，成本較低，同時又具備了豐富的功能，是物聯網應用中監控遠程設備的理想選擇。