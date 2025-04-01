import asyncio
import websockets
import json
import random
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


async def send_data(pump_id=None, custom_data=None, websocket_url="ws://127.0.0.1:7000/ws"):
    """
    發送抽水機數據到WebSocket服務器

    參數:
        pump_id: 抽水機ID, 如果是None則隨機選擇一個
        custom_data: 自定義數據，如果為None則使用預設數據
        websocket_url: WebSocket服務器URL
    """
    # 如果沒有指定pump_id，隨機選擇一個
    if pump_id is None:
        pump_id = random.choice(list(DEFAULT_TEST_DATA.keys()))

    # 獲取抽水機數據
    if custom_data is not None:
        data = custom_data
    else:
        # 如果指定了pump_id但在預設數據中不存在，使用A33的數據作為模板
        base_data = DEFAULT_TEST_DATA.get(pump_id, DEFAULT_TEST_DATA["A33"]).copy()
        base_data["d"] = pump_id

        # 隨機調整一些數據以模擬變化
        base_data["f"] = str(round(float(base_data["f"]) + random.uniform(-0.5, 0.5), 2))

        # 隨機變更狀態（10%的機率）
        if random.random() < 0.1:
            base_data["status"] = str(random.randint(1, 4))

        data = base_data

    try:
        # 與 WebSocket 伺服器建立連線
        async with websockets.connect(websocket_url) as websocket:
            # 傳送 JSON 格式的資料
            await websocket.send(json.dumps(data))
            print(f"已傳送資料: {data}")

            # 接收伺服器的回應
            response = await websocket.recv()
            print(f"接收回應: {response}")

            return response
    except Exception as e:
        print(f"連線失敗: {e}")
        return None


async def continuous_send(interval=5, count=5, pump_ids=None):
    """
    連續發送多次數據

    參數:
        interval: 發送間隔（秒）
        count: 發送次數
        pump_ids: 抽水機ID列表，如果為None則使用預設數據中的所有ID
    """
    if pump_ids is None:
        pump_ids = list(DEFAULT_TEST_DATA.keys())

    print(f"開始連續發送數據，間隔 {interval} 秒，總共 {count} 次")

    for i in range(count):
        # 隨機選擇一個抽水機ID
        pump_id = random.choice(pump_ids)

        # 發送數據
        await send_data(pump_id)

        # 如果不是最後一次，等待指定的間隔時間
        if i < count - 1:
            print(f"等待 {interval} 秒...")
            await asyncio.sleep(interval)

    print("連續發送完成")


# 命令行介面
async def main():
    print("抽水機WebSocket測試工具")
    print("=" * 30)
    print("1. 發送單一抽水機數據")
    print("2. 連續發送多次數據")
    print("3. 發送所有預設抽水機數據")
    print("4. 退出")

    choice = input("請選擇操作 (1-4): ")

    if choice == "1":
        pump_id = input("請輸入抽水機ID (按Enter使用隨機ID): ")
        if not pump_id:
            pump_id = None
        await send_data(pump_id)

    elif choice == "2":
        interval = float(input("請輸入發送間隔（秒，預設5）: ") or "5")
        count = int(input("請輸入發送次數（預設5）: ") or "5")
        await continuous_send(interval, count)

    elif choice == "3":
        print("發送所有預設抽水機數據")
        for pump_id in DEFAULT_TEST_DATA.keys():
            print(f"發送 {pump_id} 數據...")
            await send_data(pump_id)
            await asyncio.sleep(1)  # 稍微等待以避免過快發送

    elif choice == "4":
        print("程式結束")
        return

    else:
        print("無效選擇，請重新運行程式")


# 執行主程式
if __name__ == "__main__":
    asyncio.run(main())