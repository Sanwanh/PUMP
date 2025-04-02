# 抽水機監控系統使用指南

## 系統概述

本系統是一個用於監控抽水機狀態的網頁應用程式，能夠接收抽水機傳來的資料，並透過前端介面和API進行顯示和管理。主要功能包括：

1. **資料接收與儲存**：可透過WebSocket、HTTP GET或POST接收抽水機的狀態資料
2. **資料顯示**：提供網頁介面顯示所有抽水機的即時狀態
3. **JSON API**：提供標準化的JSON格式資料，可供外部系統整合
4. **自定義顯示順序**：支援自定義抽水機的顯示順序和選擇顯示哪些抽水機
5. **A100+ID支援**：支援顯示A100以上編號的抽水機

## 系統架構

### 檔案架構
```
抽水機監控系統/
├── main.py                # 主要應用程式邏輯
├── json_api.py            # JSON API 處理程式
├── pump_mappings.py       # 抽水機映射資料
├── test_websocket.py      # WebSocket 測試工具
├── config.json            # 使用者設定檔案
├── pumps.json             # 抽水機資料JSON檔案
├── README.md              # 說明文件
├── requirements.txt       # 程式相依套件
├── Dockerfile             # Docker 建構檔案
├── docker-compose.yml     # Docker Compose 配置檔案
├── .idea/                 # PyCharm專案設定資料夾
│   └── ...
├── templates/             # 前端頁面
│   ├── index.html         # 主頁面
│   ├── json_view.html     # JSON 顯示頁面
│   └── settings.html      # 設定頁面
└── static/                # 靜態資源 (若有需要可手動建立)
    ├── css/               # CSS 檔案
    ├── js/                # JavaScript 檔案
    └── images/            # 圖片資源
```

### 核心元件

1. **FastAPI 應用伺服器**：
   - 位於 `main.py`，提供HTTP和WebSocket服務
   - 負責處理前端請求及轉發資料

2. **資料存儲**：
   - 使用Excel檔案 (`data.xlsx`) 儲存抽水機狀態資料
   - 使用 `config.json` 儲存使用者設定

3. **前端介面**：
   - `index.html`：顯示抽水機狀態表格
   - `json_view.html`：顯示JSON API資料
   - `settings.html`：提供設定介面

4. **API服務**：
   - `json_api.py`：提供標準化JSON格式資料
   - 支援多種資料接收方式（WebSocket、HTTP GET/POST）

## 安裝指南

### 系統需求

- Python 3.9 或更高版本
- 相依套件：參見 `requirements.txt`
- Docker 和 Docker Compose (如使用容器化部署)

### 安裝步驟

1. **克隆專案**：
   ```bash
   git clone https://您的儲存庫位址/抽水機監控系統.git
   cd 抽水機監控系統
   ```

2. **安裝相依套件**：
   ```bash
   pip install -r requirements.txt
   ```

3. **確認設定檔**：
   檢查 `config.json` 是否存在，若不存在，系統會自動建立預設設定檔。

## 使用說明

### 啟動系統

#### 方法一：直接使用 Python

執行以下命令啟動系統：

```bash
python main.py
```

系統預設會在 `http://localhost:7000` 啟動，您可以通過瀏覽器訪問此地址。

#### 方法二：使用 Docker Compose

如果您已安裝 Docker 和 Docker Compose，可以使用容器化方式啟動系統，這樣不需要自行安裝 Python 和相依套件。

1. **啟動系統**：
   ```bash
   docker-compose up -d
   ```
   `-d` 參數表示在背景執行容器。

2. **查看容器狀態**：
   ```bash
   docker-compose ps
   ```
   
3. **查看日誌**：
   ```bash
   docker-compose logs -f
   ```
   `-f` 參數表示持續顯示新的日誌。

4. **重新啟動服務**：
   ```bash
   docker-compose restart
   ```

5. **停止服務**：
   ```bash
   docker-compose down
   ```

使用 Docker Compose 方式啟動後，系統同樣會在 `http://localhost:7000` 啟動，可透過瀏覽器訪問。

### 容器數據持久化

Docker Compose 設定中已經配置了數據持久化，相關文件映射如下：
- `./data:/app/data` - 數據存儲目錄
- `./config.json:/app/config.json` - 系統設定檔
- `./pumps.json:/app/pumps.json` - 抽水機資料檔案
- `./data.xlsx:/app/data.xlsx` - Excel資料檔案
- `./Datalist.xlsx:/app/Datalist.xlsx` - 抽水機列表檔案

所有資料變更都會實時保存到本地文件，即使容器重啟也不會丟失數據。

### 頁面說明

1. **主頁面** - `http://localhost:7000/`
   - 顯示所有抽水機的資料表格
   - 自動每5秒更新一次資料
   - 提供前往設定頁面的連結

2. **JSON API頁面** - `http://localhost:7000/api/json`
   - 顯示標準化的JSON格式抽水機資料
   - 可供外部系統整合使用

3. **設定頁面** - `http://localhost:7000/settings`
   - 選擇要顯示的抽水機
   - 自定義抽水機顯示順序（通過拖曳調整）
   - 儲存設定

### 資料更新方式

系統支援三種更新抽水機資料的方式：

1. **WebSocket**：
   ```javascript
   // 使用WebSocket發送資料
   const socket = new WebSocket("ws://localhost:7000/ws");
   socket.send(JSON.stringify({
     longitude: 121.534,
     latitude: 25.0736,
     status: "1",
     d: "A33",  // 抽水機ID
     e: "1",    // 油位狀態
     f: "12.5"  // 其他數值
   }));
   ```

2. **HTTP GET**（簡易更新，適合SIM7000等裝置）：
   ```
   GET http://localhost:7000/api/simple-update?lon=121.534&lat=25.0736&s=1&d=A33&e=1&f=12.5
   ```

3. **HTTP POST**：
   ```bash
   curl -X POST "http://localhost:7000/api/update" \
     -H "Content-Type: application/json" \
     -d '{"longitude":121.534,"latitude":25.0736,"status":"1","d":"A33","e":"1","f":"12.5"}'
   ```

### 測試工具

專案提供了測試工具 `test_websocket.py` 來模擬抽水機發送資料：

```bash
python test_websocket.py
```

依照提示選擇發送方式和抽水機ID即可進行測試。

## 設定自定義顯示順序

1. 訪問設定頁面 `http://localhost:7000/settings`
2. 在左側選擇要顯示的抽水機（勾選/取消勾選）
3. 在右側通過拖曳調整抽水機的顯示順序
4. 點擊「儲存設定」按鈕保存更改

設定會立即生效，並且會保存到 `config.json` 檔案中。

## 系統狀態解釋

抽水機狀態碼及其含義：

| 狀態碼 | 顯示文字 | 說明 |
|-------|---------|------|
| 0 | 離線 | 抽水機離線或未響應（超過30分鐘無更新） |
| 1 | 待命 | 抽水機在待命狀態 |
| 2 | 運送中 | 抽水機正在運送 |
| 3 | 抽水中 | 抽水機正在執行抽水作業 |
| 4 | 故障 | 抽水機發生故障 |
| 5 | 油位低電壓 | 抽水機油位低或電壓不足 |

油位狀態：
- `e=1`：油位正常
- `e=0`：油位低/離線

## API 說明

### 主要API端點

1. **獲取抽水機資料**
   - URL: `/api/data`
   - 方法: GET
   - 返回: 原始抽水機資料表格

2. **獲取JSON格式抽水機資料**
   - URL: `/api/json`
   - 方法: GET
   - 返回: 轉換後的JSON格式數據，包含抽水機位置、狀態和相關資訊

3. **獲取系統設定**
   - URL: `/api/config`
   - 方法: GET
   - 返回: 系統設定，包含顯示選項和排序

4. **更新抽水機資料（POST）**
   - URL: `/api/update`
   - 方法: POST
   - 參數: 
     - longitude: 經度
     - latitude: 緯度
     - status: 狀態代碼
     - d: 抽水機ID
     - e: 油位
     - f: 其他數值資料

5. **更新抽水機資料（GET）**
   - URL: `/api/simple-update`
   - 方法: GET
   - 參數: 
     - lon: 經度
     - lat: 緯度
     - s: 狀態代碼
     - d: 抽水機ID
     - e: 油位（選填）
     - f: 其他數值資料（選填）

6. **保存系統設定**
   - URL: `/api/save-settings`
   - 方法: POST
   - 參數: 
     - display_pumps: 要顯示的抽水機ID列表
     - display_order: 抽水機顯示順序

## 故障排除

### 常見問題

1. **資料未顯示更新**
   - 檢查是否成功啟動伺服器（是否有錯誤訊息）
   - 確認 `data.xlsx` 檔案存在且可寫入
   - 確認抽水機資料是否正確發送（可使用測試工具）

2. **抽水機顯示離線**
   - 系統將超過30分鐘未更新的抽水機標記為離線
   - 確認是否成功發送資料更新

3. **A100+ID無法顯示**
   - 確認 `json_api.py` 和 `main.py` 是否為最新版本
   - 檢查 `pump_mappings.py` 中是否包含A100+的映射

4. **設定未儲存**
   - 確認 `config.json` 檔案可寫入
   - 檢查錯誤訊息

5. **Docker 相關問題**
   - **容器無法啟動**: 檢查錯誤日誌 `docker-compose logs`
   - **端口被佔用**: 確認 7000 端口未被其他程序佔用，或在 `docker-compose.yml` 中修改端口映射
   - **容器啟動但無法訪問**: 檢查防火牆設定，確保允許 7000 端口通信

### 日誌檢查

如需檢查系統日誌：
- 直接執行方式：查看執行 `main.py` 時的終端機輸出
- Docker 方式：使用 `docker-compose logs -f pump-monitor` 查看容器日誌

## 擴展和客製化

### 新增抽水機

如需新增抽水機，請修改 `pump_mappings.py` 檔案，按照既有格式添加新的映射：

```python
"新ID": {
    "id": "顯示ID",
    "city": "縣市",
    "org": "機構代碼",
    "org_name": "機構名稱",
    "road": "地址",
    "town": "行政區"
},
```

### 修改狀態定義

如需修改狀態顯示文字，請修改 `pump_mappings.py` 檔案中的 `STATUS_MAPPING` 字典。

## 更新與維護

定期更新系統可確保功能正常和安全性：

1. 更新程式碼：
   ```bash
   git pull
   ```

2. 更新相依套件：
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. 更新 Docker 鏡像與容器：
   ```bash
   docker-compose pull  # 如果使用遠端鏡像
   docker-compose up -d --build  # 重新構建並啟動
   ```

## 聯絡方式

如有任何問題或建議，請聯絡系統維護人員。