# SmartVision 批量视频处理系统

支持多种大模型API的智能视频批量处理和分析系统。

## 功能特性

- 🎥 支持批量视频处理
- 🤖 支持多种AI模型（OpenAI、Claude、Gemini、通义千问、Moondream）
- 📊 自动生成Excel分析报告（每个视频一个Excel文件）
- 🎯 目标检测功能
- 💬 图像/视频问答功能

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置持续部署 (CD)

项目已配置完整的 CI/CD 流水线，支持自动构建和部署。

#### 启用自动部署

1. **设置 GitHub Secrets**（在仓库 Settings → Secrets and variables → Actions 中）：
   ```
   DOCKERHUB_USERNAME = 你的Docker Hub用户名
   DOCKERHUB_TOKEN = 你的Docker Hub访问令牌
   ```

2. **获取 Docker Hub 令牌**：
   - 登录 [Docker Hub](https://hub.docker.com)
   - 进入 Account Settings → Security → New Access Token
   - 创建具有读写权限的访问令牌

3. **服务器部署（可选）**：
   ```
   SERVER_HOST = 服务器IP地址
   SERVER_USERNAME = 服务器用户名
   SERVER_SSH_KEY = 服务器SSH私钥
   ```

#### 流水线功能

- ✅ **代码质量检查** - 语法检查和代码规范
- ✅ **前端构建** - 自动构建 React 应用
- ✅ **Docker 镜像构建** - 构建并推送到 Docker Hub
- ✅ **自动部署** - 部署到服务器（需配置）

详细配置请参考 [CD_SETUP.md](.github/workflows/CD_SETUP.md)

### 2. 配置API密钥

**重要**：为了保护你的API密钥安全，请使用环境变量配置，不要直接在代码中硬编码密钥。

#### 方法1：使用 .env 文件（推荐）

1. 在项目根目录创建 `.env` 文件
2. 参考 `ENV_SETUP.md` 文件，填入你的API密钥

示例：
```env
MODEL_TYPE=qwen
QWEN_API_KEY=your-api-key-here
MOONDREAM_API_KEY=your-api-key-here
```

#### 方法2：设置系统环境变量

Windows (PowerShell):
```powershell
$env:QWEN_API_KEY="your-api-key-here"
$env:MOONDREAM_API_KEY="your-api-key-here"
```

Linux/Mac:
```bash
export QWEN_API_KEY="your-api-key-here"
export MOONDREAM_API_KEY="your-api-key-here"
```

详细配置说明请查看 [ENV_SETUP.md](ENV_SETUP.md)

### 3. 启动后端服务

```bash
python backend_api.py
```

### 4. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
SmartVision/
├── backend_api.py          # Flask后端API服务
├── model_manager.py        # 模型管理器
├── config.py               # 配置文件（从环境变量读取）
├── config.py.example       # 配置文件模板
├── requirements.txt        # Python依赖
├── ENV_SETUP.md           # 环境变量配置说明
├── .gitignore             # Git忽略文件
└── frontend/              # 前端Vue应用
    ├── src/
    ├── package.json
    └── vite.config.js
```

## 安全提示

⚠️ **重要安全提示**：

1. **永远不要提交包含真实API密钥的文件到GitHub**
   - `config.py` 已被 `.gitignore` 忽略
   - `.env` 文件已被 `.gitignore` 忽略
   - 只提交 `config.py.example` 作为模板

2. **如果意外提交了密钥**：
   - 立即在对应服务商处重新生成新的API密钥
   - 删除GitHub仓库中的敏感信息

3. **使用环境变量**：
   - 推荐使用 `.env` 文件或系统环境变量
   - 不要直接在代码中硬编码密钥

## API接口

- `GET /api/health` - 健康检查
- `POST /api/query` - 图像问答
- `POST /api/video-query` - 视频直接问答
- `POST /api/batch-query` - 批量问答
- `POST /api/video-batch-query` - 批量视频直接处理
- `POST /api/detect` - 目标检测 (Moondream)
- `POST /api/export-excel` - 导出Excel文件

## 许可证

MIT License

