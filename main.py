from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import os
import json

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