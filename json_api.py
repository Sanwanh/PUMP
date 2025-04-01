from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pandas as pd
import os
from datetime import datetime
import uvicorn
import json
from pump_mappings import PUMP_MAPPING, STATUS_MAPPING

app = FastAPI()

# 設定檔案路徑
EXCEL_FILE = "data.xlsx"
DATALIST_FILE = "Datalist.xlsx"
CONFIG_FILE = "config.json"


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

        # 讀取設定檔
        config = load_config()
        display_pumps = config.get("display_pumps", [])
        display_order = config.get("display_order", [])

        # 準備結果資料
        all_pumps = {}

        # 處理每一筆抽水機資料
        for _, row in df.iterrows():
            # 獲取抽水機ID
            if "D" not in df.columns:
                continue

            pump_id = str(row["D"])  # 確保ID為字串類型

            # 如果沒有ID或不在datalist中（如果datalist存在且不為空），跳過
            if not pump_id or (datalist_ids and pump_id not in datalist_ids):
                continue

            # 如果不在顯示列表中，跳過
            if display_pumps and pump_id not in display_pumps:
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
            pump_info = PUMP_MAPPING.get(pump_id, {})

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
                "_oil": oil_value,
                "_original_id": pump_id  # 添加原始ID以便排序
            }

            all_pumps[pump_id] = api_data

        # 按照設定的順序排列結果
        result_data = []

        # 先添加已在顯示順序中的泵
        for pump_id in display_order:
            if pump_id in all_pumps:
                result_data.append(all_pumps[pump_id])

        # 再添加其餘的泵
        for pump_id, pump_data in all_pumps.items():
            if pump_id not in display_order:
                result_data.append(pump_data)

        return JSONResponse(content=result_data)

    except Exception as e:
        return JSONResponse(content={"error": f"發生錯誤: {str(e)}"}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)