from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pandas as pd
import os
from datetime import datetime
import uvicorn

app = FastAPI()

# 設定檔案路徑
EXCEL_FILE = "data.xlsx"
DATALIST_FILE = "Datalist.xlsx"

# 抽水機狀態對應
STATUS_MAPPING = {
    "0": "離線",
    "1": "待命",
    "2": "運送中",
    "3": "抽水中",
    "4": "故障",
    "5": "油位低電壓"
}

# 抽水機ID對應資訊
PUMP_MAPPINGS = {
    "A1": {
        "id": "北市-09",
        "city": "台北市",
        "org": "68",
        "org_name": "臺北市政府",
        "road": "臺北市士林區延平北路7段106巷358號",
        "town": "士林區"
    },
    "A5": {
        "id": "104-L01",
        "city": "桃園市",
        "org": "61",
        "org_name": "桃園市政府",
        "road": "桃園市政府水務局防汛場",
        "town": ""
    },
    "A6": {
        "id": "104-L02",
        "city": "桃園市",
        "org": "61",
        "org_name": "桃園市政府",
        "road": "桃園市政府水務局防汛場",
        "town": ""
    },
    "A33": {
        "id": "北市-01",
        "city": "台北市",
        "org": "68",
        "org_name": "臺北市政府",
        "road": "臺北市中山區濱江街97號",
        "town": "中山區"
    },
    # 以下可以根據PHP檔案中的完整對應關係補充其他的抽水機ID
}


@app.get("/")
async def root():
    return {"message": "抽水機資料API服務運行中"}


@app.get("/api/pumps")
async def get_pumps():
    """
    獲取抽水機資料，並轉換為符合要求的JSON格式
    """
    try:
        # 讀取抽水機資料
        if not os.path.exists(EXCEL_FILE):
            return JSONResponse(content={"error": f"找不到 {EXCEL_FILE} 檔案"}, status_code=404)

        df = pd.read_excel(EXCEL_FILE)

        # 讀取Datalist檔案，用於檢查ID是否存在
        datalist_ids = []
        try:
            if os.path.exists(DATALIST_FILE):
                datalist_df = pd.read_excel(DATALIST_FILE)
                if 'dl_no' in datalist_df.columns:
                    datalist_ids = datalist_df['dl_no'].tolist()
        except Exception as e:
            print(f"警告: 無法讀取 {DATALIST_FILE}, 錯誤: {e}")

        # 準備結果資料
        result_data = []

        # 處理每一筆抽水機資料
        for _, row in df.iterrows():
            # 獲取抽水機ID
            if "D" not in df.columns:
                continue

            pump_id = row["D"]

            # 如果沒有ID或不在datalist中（如果datalist存在），跳過
            if not pump_id or (datalist_ids and pump_id not in datalist_ids):
                continue

            # 獲取狀態值
            status_value = str(row["狀態"]) if "狀態" in df.columns else "0"

            # 檢查最後更新時間，如果超過30分鐘，設定為離線
            if "日期" in df.columns and "時間" in df.columns and row["日期"] and row["時間"]:
                try:
                    last_update = datetime.strptime(f"{row['日期']} {row['時間']}", "%Y-%m-%d %H:%M:%S")
                    minutes_diff = (datetime.now() - last_update).total_seconds() / 60
                    if minutes_diff > 30:
                        status_value = "0"  # 設為離線
                except Exception as e:
                    print(f"警告: 日期時間格式錯誤, {e}")

            # 設定狀態文字
            status_text = STATUS_MAPPING.get(status_value, "離線")

            # 設定油量值
            oil_value = "0"
            if status_value == "0":
                oil_value = "0"  # 離線時油量為0
            elif "E" in df.columns and row["E"] == "1":
                oil_value = "1"

            # 從映射中獲取設備資訊
            pump_info = PUMP_MAPPINGS.get(pump_id, {})

            # 構建API資料
            api_data = {
                "_id": pump_info.get("id", pump_id),
                "_lon": float(row["經度"]) if "經度" in df.columns and row["經度"] else 0.0,
                "_lat": float(row["緯度"]) if "緯度" in df.columns and row["緯度"] else 0.0,
                "_status": status_text,
                "_org": pump_info.get("org", ""),
                "_org_name": pump_info.get("org_name", ""),
                "_city": pump_info.get("city", ""),
                "_town": pump_info.get("town", ""),
                "_road": pump_info.get("road", ""),
                "operateat": f"{row['日期']} {row['時間']}" if "日期" in df.columns and "時間" in df.columns and row[
                    "日期"] and row["時間"] else "",
                "_oil": oil_value
            }

            result_data.append(api_data)

        return JSONResponse(content=result_data)

    except Exception as e:
        return JSONResponse(content={"error": f"發生錯誤: {str(e)}"}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)