import pandas as pd
import json
from datetime import datetime
import os


def get_pump_mapping():
    """
    返回抽水機編號（A系列）與其對應資訊的映射
    此函數包含從PHP檔案轉換的對應關係
    """
    pump_mappings = {
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
        "A9": {
            "id": "105-L03",
            "city": "桃園市",
            "org": "61",
            "org_name": "桃園市政府",
            "road": "桃園市政府水務局防汛場",
            "town": ""
        },
        "A10": {
            "id": "105-L04",
            "city": "桃園市",
            "org": "61",
            "org_name": "桃園市政府",
            "road": "桃園市政府水務局防汛場",
            "town": ""
        },
        "A11": {
            "id": "105-L05",
            "city": "桃園市",
            "org": "61",
            "org_name": "桃園市政府",
            "road": "桃園市龜山區復興三路247巷30號",
            "town": "龜山區"
        },
        # 新增其餘的對應關係，這裡只列出部分範例
        # 您可以參考PHP檔案中的完整對應關係
        "A17": {
            "id": "花蓮縣-01",
            "city": "花蓮縣",
            "org": "66",
            "org_name": "花蓮縣政府",
            "road": "花蓮縣花蓮市國盛七街1號",
            "town": "花蓮市"
        },
        "A33": {
            "id": "北市-01",
            "city": "台北市",
            "org": "68",
            "org_name": "臺北市政府",
            "road": "臺北市中山區濱江街97號",
            "town": "中山區"
        },
        "A84": {
            "id": "新竹縣-01",
            "city": "新竹縣",
            "org": "63",
            "org_name": "新竹縣政府",
            "road": "桃竹苗水情中心",
            "town": "竹北市"
        },
        "A116": {
            "id": "南投縣-01",
            "city": "南投縣",
            "org": "64",
            "org_name": "南投縣南投市清潔隊",
            "road": "南投縣南投市嶺興路36號",
            "town": "南投縣"
        }
    }

    return pump_mappings


def convert_to_json():
    """
    將data.xlsx中的抽水機資料轉換為JSON格式
    並檢查Datalist.xlsx確認ID是否存在
    """
    EXCEL_FILE = "data.xlsx"
    DATALIST_FILE = "Datalist.xlsx"
    OUTPUT_JSON = "pumps.json"

    # 檢查資料檔案是否存在
    if not os.path.exists(EXCEL_FILE):
        print(f"錯誤: 找不到 {EXCEL_FILE} 檔案")
        return

    # 嘗試讀取Datalist檔案
    try:
        datalist_df = pd.read_excel(DATALIST_FILE)
        datalist_ids = datalist_df['dl_no'].tolist() if 'dl_no' in datalist_df.columns else []
    except Exception as e:
        print(f"警告: 無法讀取 {DATALIST_FILE}, 錯誤: {e}")
        datalist_ids = []

    # 讀取抽水機資料
    try:
        df = pd.read_excel(EXCEL_FILE)
    except Exception as e:
        print(f"錯誤: 無法讀取 {EXCEL_FILE}, 錯誤: {e}")
        return

    # 獲取抽水機ID與資訊的映射
    pump_mappings = get_pump_mapping()

    # 準備結果資料
    result_data = []

    # 處理每一筆抽水機資料
    for _, row in df.iterrows():
        # 獲取抽水機ID
        pump_id = row["D"] if "D" in df.columns else ""

        # 如果沒有ID或不在datalist中，跳過
        if not pump_id or (datalist_ids and pump_id not in datalist_ids):
            continue

        # 獲取狀態值
        status_value = str(row["狀態"]) if "狀態" in df.columns else "0"
        status_text = "離線"  # 預設狀態

        # 檢查最後更新時間，如果超過30分鐘，設定為離線
        if "日期" in df.columns and "時間" in df.columns and row["日期"] and row["時間"]:
            try:
                last_update = datetime.strptime(f"{row['日期']} {row['時間']}", "%Y-%m-%d %H:%M:%S")
                minutes_diff = (datetime.now() - last_update).total_seconds() / 60
                if minutes_diff > 30:
                    status_value = "0"  # 設為離線
            except Exception as e:
                print(f"警告: 日期時間格式錯誤, {e}")

        # 油量值
        oil_value = "0"
        if "E" in df.columns and row["E"] == "1":
            oil_value = "1"

        # 狀態轉換，參考原始PHP的轉換邏輯
        if status_value == "0":
            status_text = "離線"
            oil_value = "0"
        elif status_value == "1":
            status_text = "待命"
        elif status_value == "2":
            status_text = "運送中"
        elif status_value == "3":
            status_text = "抽水中"
        elif status_value == "4":
            status_text = "故障"
        elif status_value == "5":
            status_text = "油位低電壓"

        # 從映射中獲取設備資訊
        pump_info = pump_mappings.get(pump_id, {})

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

    # 寫入JSON檔案
    try:
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as json_file:
            json.dump(result_data, json_file, ensure_ascii=False, indent=4)
        print(f"已成功將資料轉換並寫入 {OUTPUT_JSON}")
    except Exception as e:
        print(f"錯誤: 無法寫入JSON檔案, 錯誤: {e}")


if __name__ == "__main__":
    convert_to_json()