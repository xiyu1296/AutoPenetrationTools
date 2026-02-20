FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    nmap \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装uv并使用它来安装依赖
RUN pip install uv
RUN uv sync --frozen

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONPATH=/app

# 启动命令
CMD ["uv", "run", "fastapi", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
