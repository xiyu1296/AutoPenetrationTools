# 使用 Python 3.12 官方镜像作为基础镜像
FROM python:3.12-slim

# 设置作者信息
LABEL authors="李畅"
LABEL description="FastAPI 应用部署镜像"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目依赖文件
COPY pyproject.toml uv.lock ./

# 安装 uv 并使用它安装项目依赖
RUN pip install uv && \
    uv sync --frozen

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8020

# 启动命令
CMD ["uv", "run", "python", "app.py"]