from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form, Body, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import os
import json
import uvicorn
from pump_mappings import PUMP_MAPPING, STATUS_MAPPING

app = FastAPI(
    title="抽水機監控系統",
    description="用於監控抽水機狀態的系統，可以接收抽水機傳來的資料並提供JSON API",
    version="1.0.0",
    docs_url="/api-docs",
    redoc_url="/api-redoc",
)

# 設定檔案與資料夾路徑
EXCEL_FILE = "data.xlsx"
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
DATALIST_FILE = "Datalist.xlsx"
CONFIG_FILE = "config.json"

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


# 定義設定模型
class SettingsModel(BaseModel):
    display_pumps: List[str] = []
    display_order: List[str] = []


# 讀取設定檔案
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"無法讀取設定檔: {e}")

    # 如果檔案不存在或讀取失敗，返回預設設定
    return {
        "display_pumps": list(PUMP_MAPPING.keys()),
        "display_order": list(PUMP_MAPPING.keys())
    }


# 儲存設定檔案
def save_config(config_data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"儲存設定檔失敗: {e}")
        return False


# 讀取 Excel 資料
def load_data():
    return pd.read_excel(EXCEL_FILE)


# 寫入 Excel 資料
def save_data(df):
    df.to_excel(EXCEL_FILE, index=False)


# 嘗試載入datalist.xlsx
def load_datalist():
    try:
        if os.path.exists(DATALIST_FILE):
            df = pd.read_excel(DATALIST_FILE)
            return df["dl_no"].tolist() if "dl_no" in df.columns else []
    except Exception as e:
        print(f"載入Datalist.xlsx失敗: {e}")
    return []


# 將資料轉換為JSON API格式
def convert_to_api_json(df):
    datalist_ids = load_datalist()
    config = load_config()
    api_result = []

    # 用於暫存所有抽水機資料的字典
    all_pumps = {}

    for _, row in df.iterrows():
        if "D" not in df.columns:
            continue

        pump_id = str(row["D"])  # 確保ID為字串類型

        # 檢查是否在PUMP_MAPPING中
        if pump_id in PUMP_MAPPING:
            mapping = PUMP_MAPPING[pump_id]

            # 如果datalist存在且不為空，檢查是否在其中
            if datalist_ids and mapping["id"] not in datalist_ids:
                continue

            pump_status = str(row["狀態"]) if "狀態" in df.columns else "0"
            status_text = STATUS_MAPPING.get(pump_status, "未知")

            # 計算離線狀態 (超過30分鐘未更新即離線)
            try:
                if "日期" in df.columns and "時間" in df.columns and row["日期"] and row["時間"]:
                    date_str = f"{row['日期']} {row['時間']}"
                    last_update = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    minutes_diff = (datetime.now() - last_update).total_seconds() / 60

                    if minutes_diff > 30:
                        status_text = STATUS_MAPPING["0"]  # 離線
                        oil_status = "0"
                    else:
                        # E欄位對應油位狀態
                        oil_status = "0" if "E" not in df.columns or str(row["E"]) != "1" else "1"
                else:
                    oil_status = "0"
            except Exception as e:
                print(f"日期轉換錯誤: {e}")
                status_text = STATUS_MAPPING["0"]  # 預設離線
                oil_status = "0"

            # 創建API結構
            api_item = {
                "_id": mapping["id"],
                "_lon": float(row["經度"]) if "經度" in df.columns and row["經度"] else 0.0,
                "_lat": float(row["緯度"]) if "緯度" in df.columns and row["緯度"] else 0.0,
                "_status": status_text,
                "_org": mapping["org"],
                "_org_name": mapping["org_name"],
                "_city": mapping["city"],
                "_town": mapping["town"],
                "_road": mapping["road"],
                "operateat": f"{row['日期']} {row['時間']}" if "日期" in df.columns and "時間" in df.columns and row[
                    "日期"] and row["時間"] else "",
                "_oil": oil_status,
                "_original_id": pump_id  # 添加原始ID以便排序
            }

            all_pumps[pump_id] = api_item

    # 按照設定的順序排列
    for pump_id in config["display_order"]:
        if pump_id in all_pumps and (not config["display_pumps"] or pump_id in config["display_pumps"]):
            api_result.append(all_pumps[pump_id])

    # 添加任何未在排序中但存在於資料中的抽水機
    for pump_id, pump_data in all_pumps.items():
        if pump_id not in config["display_order"] and (
                not config["display_pumps"] or pump_id in config["display_pumps"]):
            api_result.append(pump_data)

    return api_result


# 主頁顯示資料表
# 主頁顯示資料表
@app.get("/", response_class=HTMLResponse)
async def read_data(request: Request):
    df = load_data()
    if df.empty:
        df = pd.DataFrame([{col: "" for col in COLUMNS}])  # 空表時自動填一行空資料

    # 讀取設定檔以獲取顯示順序
    config = load_config()
    display_pumps = config.get("display_pumps", [])
    display_order = config.get("display_order", [])

    # 轉換為字典列表
    raw_data = df.to_dict(orient="records")

    # 用於儲存排序後的資料
    ordered_data = []

    # 建立一個ID到資料行的映射
    data_map = {}
    for row in raw_data:
        if "D" in row and row["D"]:
            pump_id = str(row["D"])
            data_map[pump_id] = row

    # 首先添加顯示順序中的項目
    for pump_id in display_order:
        if pump_id in data_map and (not display_pumps or pump_id in display_pumps):
            ordered_data.append(data_map[pump_id])

    # 然後添加未在顯示順序中但應該顯示的項目
    for pump_id, row in data_map.items():
        if pump_id not in display_order and (not display_pumps or pump_id in display_pumps):
            ordered_data.append(row)

    # 如果沒有資料，使用原始資料
    if not ordered_data:
        ordered_data = raw_data

    return templates.TemplateResponse("index.html", {"request": request, "data": ordered_data})


# 提供資料 API
@app.get("/api/data", tags=["資料API"])
async def get_data():
    """
    獲取原始抽水機資料表格
    """
    df = load_data()
    if df.empty:
        df = pd.DataFrame([{col: "" for col in COLUMNS}])  # 空表時自動填一行空資料
    return df.to_dict(orient="records")


# 提供JSON API (類似PHP的輸出)
@app.get("/api/json", tags=["資料API"])
async def get_json_api():
    """
    獲取轉換後的JSON格式數據，包含抽水機位置、狀態和相關資訊
    """
    df = load_data()
    if df.empty:
        return []

    api_data = convert_to_api_json(df)
    return api_data

# 提供設定檔 API
@app.get("/api/config", tags=["系統設定"])
async def get_config():
    """
    獲取系統設定，包含顯示選項和排序
    """
    return load_config()


# JSON資料顯示頁面 (純JSON顯示)
@app.get("/json", response_class=RedirectResponse)
async def json_redirect():
    """
    重定向到純JSON API頁面
    """
    return RedirectResponse(url="/api/json")


# 接收HTTP POST請求更新抽水機資料
@app.post("/api/update", tags=["資料更新"])
async def update_data(data: DataModel):
    """
    通過HTTP POST更新抽水機資料

    - **longitude**: 經度
    - **latitude**: 緯度
    - **status**: 狀態代碼 (0-5)
    - **d**: 抽水機ID (例如: A33)
    - **e**: 油位 (1:正常, 0:低)
    - **f**: 其他數值資料
    """
    try:
        df = load_data()
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        # 創建新資料
        new_entry = {
            "經度": data.longitude,
            "緯度": data.latitude,
            "狀態": data.status,
            "D": data.d,
            "E": data.e,
            "F": data.f,
            "日期": current_date,
            "時間": current_time,
        }

        # 檢查 D 欄位是否已存在
        existing_entry = df[df["D"] == data.d] if not df.empty and "D" in df.columns else pd.DataFrame()

        if not existing_entry.empty:
            # 如果 D 已存在，更新該筆資料
            index = existing_entry.index[0]
            for key, value in new_entry.items():
                df.at[index, key] = value
            message = f"資料已更新: D={data.d}"
        else:
            # 如果 D 不存在，新增一筆資料
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            message = f"資料已新增: D={data.d}"

        # 儲存更新後的資料
        save_data(df)
        return {"status": "success", "message": message}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# 接收簡單的GET請求更新抽水機資料 (適合SIM7000等裝置)
@app.get("/api/simple-update", tags=["資料更新"])
async def simple_update(lon: float, lat: float, s: str, d: str, e: str = "0", f: str = "0"):
    """
    通過簡單的GET請求更新抽水機資料，適合SIM7000等裝置

    - **lon**: 經度
    - **lat**: 緯度
    - **s**: 狀態代碼 (0-5)
    - **d**: 抽水機ID (例如: A33)
    - **e**: 油位 (1:正常, 0:低) (選填)
    - **f**: 其他數值資料 (選填)
    """
    try:
        df = load_data()
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        # 創建新資料
        new_entry = {
            "經度": lon,
            "緯度": lat,
            "狀態": s,
            "D": d,
            "E": e,
            "F": f,
            "日期": current_date,
            "時間": current_time,
        }

        # 檢查 D 欄位是否已存在
        existing_entry = df[df["D"] == d] if not df.empty and "D" in df.columns else pd.DataFrame()

        if not existing_entry.empty:
            # 如果 D 已存在，更新該筆資料
            index = existing_entry.index[0]
            for key, value in new_entry.items():
                df.at[index, key] = value
            message = f"資料已更新: D={d}"
        else:
            # 如果 D 不存在，新增一筆資料
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            message = f"資料已新增: D={d}"

        # 儲存更新後的資料
        save_data(df)
        return {"status": "success", "message": message}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# 設定頁面
@app.get("/settings", response_class=HTMLResponse, tags=["系統設定"])
async def settings_page(request: Request):
    """
    顯示系統設定頁面，可以配置抽水機顯示順序和顯示選項
    """
    config = load_config()
    all_pumps = [{"id": k, "name": v["id"]} for k, v in PUMP_MAPPING.items()]

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": config,
        "all_pumps": all_pumps,
        "current_order": config["display_order"]
    })


# 保存設定
@app.post("/api/save-settings", tags=["系統設定"])
async def save_settings(settings: Dict = Body(...)):
    """
    保存系統設定

    - **display_pumps**: 要顯示的抽水機ID列表
    - **display_order**: 抽水機顯示順序
    """
    try:
        config = {
            "display_pumps": settings.get("display_pumps", []),
            "display_order": settings.get("display_order", [])
        }

        if save_config(config):
            return {"status": "success", "message": "設定已保存"}
        else:
            return {"status": "error", "message": "保存設定失敗"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# WebSocket 接收資料 (保留原有功能)
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
                existing_entry = df[df["D"] == data_dict["d"]] if not df.empty and "D" in df.columns else pd.DataFrame()

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