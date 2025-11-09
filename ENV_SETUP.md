# 环境变量配置说明

为了保护你的API密钥安全，本项目使用环境变量来存储敏感信息。

## 快速开始

### 方法1：使用 .env 文件（推荐）

1. 在项目根目录创建 `.env` 文件
2. 复制以下内容到 `.env` 文件，并填入你的真实API密钥：

```env
# 模型选择 (moondream, openai, claude, gemini, qwen)
MODEL_TYPE=qwen

# Moondream API 配置
MOONDREAM_API_KEY=your-moondream-api-key-here

# OpenAI API 配置
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Claude API 配置
CLAUDE_API_KEY=your-claude-api-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Gemini API 配置
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-pro

# 通义千问 API 配置
QWEN_API_KEY=your-qwen-api-key-here
QWEN_MODEL=qwen3-vl-plus-2025-09-23

# FFmpeg路径（可选，默认使用系统PATH中的ffmpeg）
FFMPEG_PATH=ffmpeg

# 临时文件目录（可选）
SMARTVISION_TEMP_DIR=

# 默认图像路径（可选）
DEFAULT_IMAGE_PATH=
```

3. 安装 python-dotenv 包来加载 .env 文件：
```bash
pip install python-dotenv
```

4. 在 `backend_api.py` 开头添加：
```python
from dotenv import load_dotenv
load_dotenv()
```

### 方法2：直接设置系统环境变量

#### Windows (PowerShell)
```powershell
$env:MODEL_TYPE="qwen"
$env:QWEN_API_KEY="your-api-key-here"
$env:MOONDREAM_API_KEY="your-api-key-here"
```

#### Windows (CMD)
```cmd
set MODEL_TYPE=qwen
set QWEN_API_KEY=your-api-key-here
set MOONDREAM_API_KEY=your-api-key-here
```

#### Linux/Mac
```bash
export MODEL_TYPE=qwen
export QWEN_API_KEY=your-api-key-here
export MOONDREAM_API_KEY=your-api-key-here
```

### 方法3：使用 config.py（不推荐，仅用于本地开发）

1. 复制 `config.py.example` 为 `config.py`
2. 在 `config.py` 中直接填入API密钥（注意：不要提交到GitHub！）

## 必需的环境变量

根据你选择的模型，需要设置相应的API密钥：

- **Moondream**: `MOONDREAM_API_KEY`（必需，用于目标检测）
- **OpenAI**: `OPENAI_API_KEY`（如果使用OpenAI模型）
- **Claude**: `CLAUDE_API_KEY`（如果使用Claude模型）
- **Gemini**: `GEMINI_API_KEY`（如果使用Gemini模型）
- **通义千问**: `QWEN_API_KEY`（如果使用通义千问模型）

## 可选的环境变量

- `MODEL_TYPE`: 模型类型，默认为 "qwen"
- `FFMPEG_PATH`: FFmpeg可执行文件路径，默认为 "ffmpeg"
- `SMARTVISION_TEMP_DIR`: 临时文件目录
- `DEFAULT_IMAGE_PATH`: 默认图像路径

## 安全提示

⚠️ **重要**：
- 永远不要将包含真实API密钥的 `config.py` 或 `.env` 文件提交到GitHub
- 如果意外提交了密钥，请立即在对应服务商处重新生成新的API密钥
- `.env` 和 `config.py` 已被 `.gitignore` 忽略，不会被提交

