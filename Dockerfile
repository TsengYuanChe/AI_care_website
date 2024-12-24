# 使用輕量級 Python 映像
FROM python:3.12

RUN apt-get update && \
    apt-get install -y libgl1 && \
    rm -rf /var/lib/apt/lists/*
# 設置工作目錄
WORKDIR /app

# 複製需求文件到容器中
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 複製整個應用到容器
COPY . .

# 設置環境變量
ENV FLASK_APP="apps.app:create_app('local')"
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080

# 暴露 8080 埠
EXPOSE 8080

# 使用 Gunicorn 啟動應用
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "apps.app:create_app('local')"]