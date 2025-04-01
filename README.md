# 抽水機監控系統修改說明

## 主要修改內容

1. **JSON API 純顯示**
   - 修改 `/json` 端點直接重定向到 `/api/json`，確保顯示純 JSON 格式資料
   - 移除了複雜的 JSON 視圖頁面

2. **新增 API 文件**
   - 在 FastAPI 初始化時加入了 `docs_url` 和 `redoc_url` 參數
   - 新增了 `/api-docs` 和 `/api-redoc` 端點，用於顯示 API 文檔
   - 為所有 API 端點添加了詳細的文檔描述和參數說明

3. **新增 HTTP 介面 (支援 SIM7000)**
   - 新增 `/api/update` (POST) 端點接收抽水機資料
   - 新增 `/api/simple-update` (GET) 端點，專為 SIM7000 等支援 HTTP 但不支援 WebSocket 的裝置設計
   - 保留原有的 WebSocket 功能，確保兼容性

4. **簡化測試工具**
   - 將測試工具簡化為三個主要功能：WebSocket、HTTP GET 和 HTTP POST
   - 保留基本資料模型和隨機選擇功能

## 使用說明

### API 端點

- `/api/data`: 獲取原始資料表格
- `/api/json`: 獲取轉換後的 JSON 格式資料
- `/api/update`: 通過 POST 方法更新抽水機資料
- `/api/simple-update`: 通過 GET 方法更新抽水機資料，適合 SIM7000 裝置

### SIM7000 設備發送資料示例

SIM7000 設備可以通過以下 HTTP GET 請求發送資料：

```
http://[您的伺服器網址]:7000/api/simple-update?lon=121.534&lat=25.0736&s=1&d=A33&e=1&f=12.5
```

必要參數說明：
- `lon`: 經度
- `lat`: 緯度
- `s`: 狀態代碼
- `d`: 抽水機ID
- `e`: 油位狀態 (選填)
- `f`: 其他資料 (選填)

### 查看 API 文件

訪問以下網址查看完整 API 文件：
- Swagger UI: `http://[您的伺服器網址]:7000/api-docs`
- ReDoc: `http://[您的伺服器網址]:7000/api-redoc`