import asyncio
import websockets
import json
import random


async def send_data(use_existing_d=False):
    # WebSocket 伺服器 URL
    uri = "ws://127.0.0.1:8000/ws"

    # 要傳送的資料
    if use_existing_d:
        # 使用已存在的 D 值 "A33" 測試更新功能
        data = {
            "longitude": 121.534,  # 修改成新的經度
            "latitude": 25.0736,  # 修改成新的緯度
            "status": 1,
            "d": "A33",  # 保持已存在的 D 值
            "e": 0,
            "f": 12.87  # 修改成新的 F 值
        }
    try:
        # 與 WebSocket 伺服器建立連線
        async with websockets.connect(uri) as websocket:
            # 傳送 JSON 格式的資料
            await websocket.send(json.dumps(data))
            print(f"已傳送資料: {data}")

            # 接收伺服器的回應
            response = await websocket.recv()
            print(f"接收回應: {response}")
    except Exception as e:
        print(f"連線失敗: {e}")

# 執行發送函數
async def main():
    # 首先測試更新已存在的 D 值
    print("測試 1: 更新已存在的資料 (D=A33)")
    await send_data(use_existing_d=True)


# 執行測試
asyncio.run(main())