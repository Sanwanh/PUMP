# 使用Python 3.9作為基礎映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 安裝所需的依賴項
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案
COPY . .

# 暴露應用程式的連接埠
EXPOSE 7000

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 啟動應用程式
CMD ["python", "main.py"]