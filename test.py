import asyncio
import websockets
import json

async def send_data():
    # WebSocket 伺服器 URL
    uri = "ws://127.0.0.1:8000/ws"

    # 要傳送的資料
    data = {
        "longitude": 121.5654,
        "latitude": 25.033,
        "status": 1,
        "d": "A33",
        "e": 0,
        "f": 12.55
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
asyncio.run(send_data())