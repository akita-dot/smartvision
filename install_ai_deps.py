#!/usr/bin/env python3
"""
AI 模型依赖动态安装脚本
在容器启动时按需安装 AI 模型库，避免构建时下载大文件
"""

import subprocess
import sys
import os

def install_ai_dependencies():
    """安装 AI 模型相关依赖"""
    ai_deps = [
        "torch",
        "transformers",
        "openai",
        "anthropic", 
        "google-generativeai",
        "dashscope",
        "moondream",
        "opencv-python",
        "imageio",
        "imageio-ffmpeg"
    ]
    
    print("开始安装 AI 模型依赖...")
    
    for dep in ai_deps:
        try:
            print(f"安装 {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", dep])
            print(f"✓ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"✗ {dep} 安装失败: {e}")
            # 继续安装其他依赖
            continue
    
    print("AI 模型依赖安装完成")

if __name__ == "__main__":
    # 检查是否需要安装 AI 依赖
    if os.getenv("INSTALL_AI_DEPS", "false").lower() == "true":
        install_ai_dependencies()
    else:
        print("跳过 AI 依赖安装 (设置 INSTALL_AI_DEPS=true 启用)")