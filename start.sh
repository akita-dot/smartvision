#!/bin/bash

# SmartVision 容器启动脚本
# 支持按需安装 AI 模型依赖

echo "=== SmartVision 启动脚本 ==="

# 检查是否需要安装 AI 依赖
if [ "$INSTALL_AI_DEPS" = "true" ]; then
    echo "检测到 INSTALL_AI_DEPS=true，开始安装 AI 模型依赖..."
    python install_ai_deps.py
    
    # 检查安装是否成功
    if [ $? -eq 0 ]; then
        echo "✓ AI 模型依赖安装成功"
    else
        echo "⚠ AI 模型依赖安装失败，但将继续启动应用"
    fi
else
    echo "跳过 AI 模型依赖安装 (设置 INSTALL_AI_DEPS=true 启用)"
fi

# 启动应用
echo "启动 SmartVision 应用..."
exec python backend_api.py