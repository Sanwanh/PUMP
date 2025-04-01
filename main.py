from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import os
import json
import uvicorn

app = FastAPI()

# 設定檔案與資料夾路徑
EXCEL_FILE = "data.xlsx"
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"

COLUMNS = ["經度", "緯度", "狀態", "D", "E", "F", "日期", "時間"]

# 初始化資料庫
if not os.path.exists(EXCEL_FILE):
    pd.DataFrame(columns=COLUMNS).to_excel(EXCEL_FILE, index=False)

# 設定 templates 與 static 資源
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# 定義資料模型
class DataModel(BaseModel):
    longitude: float
    latitude: float
    status: str
    d: str
    e: str
    f: str


# 讀取 Excel 資料
def load_data():
    return pd.read_excel(EXCEL_FILE)


# 寫入 Excel 資料
def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)


# 狀態碼對應表（從PHP代碼中提取）
STATUS_MAPPING = {
    "0": "離線",
    "1": "待命",
    "2": "運送中",
    "3": "抽水中",
    "4": "故障",
    "5": "油位低電壓"
}

# 抽水機ID對應表（從PHP代碼中提取）
PUMP_MAPPING = {
    "A1": {"id": "北市-09", "city": "台北市", "org": "68", "org_name": "臺北市政府",
           "road": "臺北市士林區延平北路7段106巷358號", "town": "士林區"},
    "A5": {"id": "104-L01", "city": "桃園市", "org": "61", "org_name": "桃園市政府", "road": "桃園市政府水務局防汛場",
           "town": ""},
    "A6": {"id": "104-L02", "city": "桃園市", "org": "61", "org_name": "桃園市政府", "road": "桃園市政府水務局防汛場",
           "town": ""},
    "A9": {"id": "105-L03", "city": "桃園市", "org": "61", "org_name": "桃園市政府", "road": "桃園市政府水務局防汛場",
           "town": ""},
    "A10": {"id": "105-L04", "city": "桃園市", "org": "61", "org_name": "桃園市政府", "road": "桃園市政府水務局防汛場",
            "town": ""},
    "A11": {"id": "105-L05", "city": "桃園市", "org": "61", "org_name": "桃園市政府",
            "road": "桃園市龜山區復興三路247巷30號", "town": "龜山區"},
    "A12": {"id": "105-L06", "city": "桃園市", "org": "61", "org_name": "桃園市政府", "road": "桃園市政府水務局防汛場",
            "town": ""},
    "A13": {"id": "105-L07", "city": "桃園市", "org": "61", "org_name": "桃園市政府", "road": "桃園市政府水務局防汛場",
            "town": ""},
    "A14": {"id": "105-L08", "city": "桃園市", "org": "61", "org_name": "桃園市政府",
            "road": "桃園市龜山區復興三路247巷30號", "town": "龜山區"},
    "A15": {"id": "105-L09", "city": "桃園市", "org": "61", "org_name": "桃園市政府", "road": "桃園市政府水務局防汛場",
            "town": ""},
    "A17": {"id": "花蓮縣-01", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府",
            "road": "花蓮縣花蓮市國盛七街1號", "town": "花蓮市"},
    "A18": {"id": "花蓮縣-02", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府",
            "road": "花蓮縣吉安鄉南濱路一段531號", "town": "吉安鄉"},
    "A19": {"id": "吉安鄉-03", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府",
            "road": "花蓮縣吉安鄉中山路三段953巷2號", "town": "吉安鄉"},
    "A20": {"id": "吉安鄉-04", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府",
            "road": "花蓮縣吉安鄉中山路三段953巷2號", "town": "吉安鄉"},
    "A21": {"id": "花蓮縣-05", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府",
            "road": "花蓮縣吉安鄉中山路三段953巷2號", "town": "吉安鄉"},
    "A22": {"id": "花蓮縣-06", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府",
            "road": "花蓮縣鳳林鎮榮開路70號", "town": "鳳林鎮"},
    "A23": {"id": "花蓮縣-07", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府",
            "road": "花蓮縣鳳林鎮榮開路70號", "town": "鳳林鎮"},
    "A24": {"id": "花蓮縣-08", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府", "road": "花蓮縣玉里鎮清潔隊",
            "town": "玉里鎮"},
    "A25": {"id": "花蓮縣-09", "city": "花蓮縣", "org": "66", "org_name": "花蓮縣政府", "road": "花蓮縣玉里鎮清潔隊",
            "town": "玉里鎮"},
    "A33": {"id": "北市-01", "city": "台北市", "org": "68", "org_name": "臺北市政府", "road": "臺北市中山區濱江街97號",
            "town": "中山區"},
    "A34": {"id": "北市-02", "city": "台北市", "org": "68", "org_name": "臺北市政府", "road": "臺北市中山區濱江街97號",
            "town": "中山區"},
    "A35": {"id": "北市-03", "city": "台北市", "org": "68", "org_name": "臺北市政府",
            "road": "臺北市士林區中山北路6段2巷1號", "town": "士林區"},
    "A36": {"id": "北市-04", "city": "台北市", "org": "68", "org_name": "臺北市政府",
            "road": "臺北市士林區中山北路6段2巷1號", "town": "士林區"},
    "A37": {"id": "北市-05", "city": "台北市", "org": "68", "org_name": "臺北市政府",
            "road": "臺北市士林區中山北路6段2巷1號", "town": "士林區"},
    "A38": {"id": "北市-06", "city": "台北市", "org": "68", "org_name": "臺北市政府", "road": "臺北市中山區濱江街97號",
            "town": "中山區"},
    "A39": {"id": "北市-07", "city": "台北市", "org": "68", "org_name": "臺北市政府",
            "road": "臺北市士林區中山北路6段2巷1號", "town": "士林區"},
    "A40": {"id": "北市-08", "city": "台北市", "org": "68", "org_name": "臺北市政府", "road": "臺北市中山區濱江街97號",
            "town": "中山區"},
    # 此處省略其他大量映射關係...
}


# 嘗試載入datalist.xlsx
def load_datalist():
    try:
        if os.path.exists("Datalist.xlsx"):
            df = pd.read_excel("Datalist.xlsx")
            return df["dl_no"].tolist() if "dl_no" in df.columns else []
    except Exception as e:
        print(f"載入Datalist.xlsx失敗: {e}")
    return []


# 將資料轉換為JSON API格式
def convert_to_api_json(df):
    datalist_ids = load_datalist()
    api_result = []

    for _, row in df.iterrows():
        pump_id = row["D"]
        # 檢查是否在PUMP_MAPPING中
        if pump_id in PUMP_MAPPING:
            mapping = PUMP_MAPPING[pump_id]
            pump_status = str(row["狀態"])
            status_text = STATUS_MAPPING.get(pump_status, "未知")

            # 計算離線狀態 (超過30分鐘未更新即離線)
            try:
                date_str = f"{row['日期']} {row['時間']}"
                last_update = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                minutes_diff = (datetime.now() - last_update).total_seconds() / 60

                if minutes_diff > 30:
                    status_text = STATUS_MAPPING["0"]  # 離線
                    oil_status = "0"
                else:
                    # E欄位對應油位狀態
                    oil_status = "0" if str(row["E"]) != "1" else "1"
            except Exception as e:
                print(f"日期轉換錯誤: {e}")
                status_text = STATUS_MAPPING["0"]  # 預設離線
                oil_status = "0"

            # 創建API結構
            api_item = {
                "_id": mapping["id"],
                "_lon": row["經度"],
                "_lat": row["緯度"],
                "_status": status_text,
                "_org": mapping["org"],
                "_org_name": mapping["org_name"],
                "_city": mapping["city"],
                "_town": mapping["town"],
                "_road": mapping["road"],
                "operateat": f"{row['日期'].replace('-', '/')} {row['時間']}",
                "_oil": oil_status
            }

            # 只保留在datalist中的ID
            if not datalist_ids or mapping["id"] in datalist_ids:
                api_result.append(api_item)

    return api_result


# 主頁顯示資料表
@app.get("/", response_class=HTMLResponse)
async def read_data(request: Request):
    df = load_data()
    if df.empty:
        df = pd.DataFrame([{col: "" for col in COLUMNS}])  # 空表時自動填一行空資料
    data = df.to_dict(orient="records")
    return templates.TemplateResponse("index.html", {"request": request, "data": data})


# 提供資料 API
@app.get("/api/data")
async def get_data():
    df = load_data()
    if df.empty:
        df = pd.DataFrame([{col: "" for col in COLUMNS}])  # 空表時自動填一行空資料
    return df.to_dict(orient="records")


# 提供JSON API (類似PHP的輸出)
@app.get("/api/json")
async def get_json_api():
    df = load_data()
    if df.empty:
        return []

    api_data = convert_to_api_json(df)
    return api_data


# JSON資料顯示頁面
@app.get("/json-view", response_class=HTMLResponse)
async def json_view(request: Request):
    return templates.TemplateResponse("json_view.html", {"request": request})


# WebSocket 接收資料
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            data_dict = json.loads(data)
            try:
                df = load_data()
                current_date = datetime.now().strftime("%Y-%m-%d")
                current_time = datetime.now().strftime("%H:%M:%S")

                # 創建新資料
                new_entry = {
                    "經度": data_dict["longitude"],
                    "緯度": data_dict["latitude"],
                    "狀態": data_dict["status"],
                    "D": data_dict["d"],
                    "E": data_dict["e"],
                    "F": data_dict["f"],
                    "日期": current_date,
                    "時間": current_time,
                }

                # 檢查 D 欄位是否已存在
                existing_entry = df[df["D"] == data_dict["d"]]

                if not existing_entry.empty:
                    # 如果 D 已存在，更新該筆資料
                    index = existing_entry.index[0]
                    for key, value in new_entry.items():
                        df.at[index, key] = value
                    await websocket.send_text(f"資料已更新: D={data_dict['d']}")
                else:
                    # 如果 D 不存在，新增一筆資料
                    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                    await websocket.send_text(f"資料已新增: D={data_dict['d']}")

                # 儲存更新後的資料
                save_data(df)

            except Exception as e:
                await websocket.send_text(f"錯誤: {str(e)}")
    except WebSocketDisconnect:
        print("Client disconnected")


# 啟動服務器
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)