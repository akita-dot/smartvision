# 多阶段构建 Dockerfile
# 阶段1: 构建前端
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖
RUN npm ci

# 复制前端源代码
COPY frontend/ ./

# 构建前端
RUN npm run build

# 阶段2: Python 后端
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 依赖文件
COPY requirements-ci.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements-ci.txt

# 复制后端代码、安装脚本和启动脚本
COPY backend_api.py model_manager.py config.py install_ai_deps.py start.sh ./

# 从构建阶段复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 设置启动脚本执行权限
RUN chmod +x start.sh

# 创建必要的目录
RUN mkdir -p uploads

# 设置环境变量（默认值，实际值通过环境变量或 secrets 传入）
ENV MODEL_TYPE=qwen
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5000

# 启动命令（使用启动脚本）
CMD ["./start.sh"]










