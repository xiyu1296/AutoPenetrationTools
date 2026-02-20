@echo off
REM FastAPI 应用部署脚本 (Windows)

echo 🚀 开始部署 FastAPI 应用...

REM 创建必要的目录
mkdir logs 2>nul
mkdir data 2>nul

REM 构建并启动服务
echo 🐳 构建 Docker 镜像...
docker-compose build

echo 🔄 启动服务...
docker-compose up -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 📋 服务状态:
docker-compose ps

echo ✅ 部署完成!
echo 查看地址: http://localhost:8020
echo API文档: http://localhost:8020/docs
echo 停止服务: docker-compose down

pause