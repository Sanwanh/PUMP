import asyncio
import websockets
import json
import random
import requests
from datetime import datetime

# 預設測試數據
DEFAULT_TEST_DATA = {
    "A33": {  # 北市-01
        "longitude": 121.534,
        "latitude": 25.0736,
        "status": "1",  # 待命
        "d": "A33",
        "e": "1",  # 油位正常
        "f": "12.5"
    },
    "A1": {  # 北市-09
        "longitude": 121.498,
        "latitude": 25.0921,
        "status": "3",  # 抽水中
        "d": "A1",
        "e": "1",  # 油位正常
        "f": "10.2"
    },
    "A5": {  # 104-L01
        "longitude": 121.324,
        "latitude": 24.9876,
        "status": "2",  # 運送中
        "d": "A5",
        "e": "0",  # 油位低
        "f": "8.7"
    }
}


async def send_websocket_data(pump_id=None, websocket_url="ws://127.0.0.1:7000/ws"):
    """
    通過WebSocket發送抽水機數據
    """
    if pump_id is None:
        pump_id = random.choice(list(DEFAULT_TEST_DATA.keys()))

    data = DEFAULT_TEST_DATA.get(pump_id, DEFAULT_TEST_DATA["A33"]).copy()
    data["d"] = pump_id

    try:
        async with websockets.connect(websocket_url) as websocket:
            await websocket.send(json.dumps(data))
            print(f"已傳送WebSocket資料: {data}")
            response = await websocket.recv()
            print(f"接收回應: {response}")
            return response
    except Exception as e:
        print(f"WebSocket連線失敗: {e}")
        return None


def send_http_data(pump_id=None, url="http://127.0.0.1:7000/api/simple-update"):
    """
    通過HTTP GET請求發送抽水機數據 (適合SIM7000等裝置)
    """
    if pump_id is None:
        pump_id = random.choice(list(DEFAULT_TEST_DATA.keys()))

    data = DEFAULT_TEST_DATA.get(pump_id, DEFAULT_TEST_DATA["A33"]).copy()
    data["d"] = pump_id

    # 構建GET請求參數
    params = {
        "lon": data["longitude"],
        "lat": data["latitude"],
        "s": data["status"],
        "d": data["d"],
        "e": data["e"],
        "f": data["f"]
    }

    # 組成完整URL
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])
    full_url = f"{url}?{query_string}"

    try:
        response = requests.get(url, params=params)
        print(f"已傳送HTTP資料: {params}")
        print(f"完整URL: {full_url}")
        print(f"接收回應: {response.text}")
        return response.text
    except Exception as e:
        print(f"HTTP請求失敗: {e}")
        return None

def send_http_post_data(pump_id=None, url="http://127.0.0.1:7000/api/update"):
    """
    通過HTTP POST請求發送抽水機數據
    """
    if pump_id is None:
        pump_id = random.choice(list(DEFAULT_TEST_DATA.keys()))

    data = DEFAULT_TEST_DATA.get(pump_id, DEFAULT_TEST_DATA["A33"]).copy()
    data["d"] = pump_id

    try:
        response = requests.post(url, json=data)
        print(f"已傳送HTTP POST資料: {data}")
        print(f"接收回應: {response.text}")
        return response.text
    except Exception as e:
        print(f"HTTP POST請求失敗: {e}")
        return None


# 命令行介面
async def main():
    print("抽水機數據測試工具")
    print("=" * 30)
    print("1. 使用WebSocket發送數據")
    print("2. 使用HTTP GET發送數據 (適合SIM7000)")
    print("3. 使用HTTP POST發送數據")
    print("4. 退出")

    choice = input("請選擇操作 (1-4): ")

    if choice == "1":
        pump_id = input("請輸入抽水機ID (按Enter使用隨機ID): ")
        if not pump_id:
            pump_id = None
        await send_websocket_data(pump_id)

    elif choice == "2":
        pump_id = input("請輸入抽水機ID (按Enter使用隨機ID): ")
        if not pump_id:
            pump_id = None
        send_http_data(pump_id)

    elif choice == "3":
        pump_id = input("請輸入抽水機ID (按Enter使用隨機ID): ")
        if not pump_id:
            pump_id = None
        send_http_post_data(pump_id)

    elif choice == "4":
        print("程式結束")
        return

    else:
        print("無效選擇，請重新運行程式")


# 執行主程式
if __name__ == "__main__":
    asyncio.run(main())