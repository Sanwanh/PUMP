# 抽水機監控系統

這是一個用於監控抽水機狀態的系統，可以接收抽水機傳來的資料並提供JSON API。

## 系統功能

- 接收抽水機資料（位置、狀態、油位等）
- 將資料保存到Excel檔案中
- 提供JSON API介面
- 根據Datalist.xlsx過濾顯示的抽水機
- 提供網頁介面查看數據和JSON格式

## 安裝與設定

### 系統需求

- Python 3.9或更高版本
- 相關Python套件（見requirements.txt）

### 安裝步驟

1. 克隆或下載此專案
2. 安裝依賴套件：

```bash
pip install -r requirements.txt
```

3. 確保以下檔案存在：
   - data.xlsx (若不存在會自動創建)
   - Datalist.xlsx (可選，用於過濾顯示的抽水機)

## 使用說明

### 啟動系統

```bash
python main.py
```

系統會在 `http://localhost:7000` 啟動。

### 網頁介面

- 主頁 (`/`): 顯示所有抽水機資料表格
- JSON視圖 (`/json-view`): 查看JSON格式的數據和統計資訊

### API端點

- `/api/data`: 獲取原始資料表格
- `/api/json`: 獲取轉換後的JSON格式數據

### WebSocket接口

系統提供WebSocket接口接收抽水機數據：
- WebSocket URL: `ws://localhost:7000/ws`
- 數據格式範例:
```json
{
  "longitude": 121.534,
  "latitude": 25.0736,
  "status": "1",
  "d": "A33",
  "e": "1",
  "f": "12.5"
}
```

### 測試工具

使用測試工具發送模擬數據：

```bash
python test_websocket.py
```

## 檔案結構

- `main.py`: 主應用程式
- `json_api.py`: JSON API服務
- `pump_mappings.py`: 抽水機ID對應表
- `test_websocket.py`: WebSocket測試工具
- `data.xlsx`: 抽水機資料存儲
- `Datalist.xlsx`: 抽水機ID清單
- `templates/`: HTML模板
  - `index.html`: 資料表視圖
  - `json_view.html`: JSON視圖
- `static/`: 靜態資源

## 狀態代碼說明

抽水機狀態對應表：
- `0`: 離線
- `1`: 待命
- `2`: 運送中
- `3`: 抽水中
- `4`: 故障
- `5`: 油位低電壓