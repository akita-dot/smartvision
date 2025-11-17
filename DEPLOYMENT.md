# 部署指南

## GitHub Secrets 配置

### 步骤1: 进入 GitHub 仓库设置

1. 打开你的 GitHub 仓库
2. 点击 **Settings** > **Secrets and variables** > **Actions**
3. 点击 **New repository secret** 添加以下密钥

### 方式1: SSH 部署（推荐用于 VPS/云服务器）

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `DEPLOY_HOST` | 服务器IP或域名 | `192.168.1.100` 或 `example.com` |
| `DEPLOY_USER` | SSH用户名 | `ubuntu` 或 `root` |
| `DEPLOY_SSH_KEY` | SSH私钥内容 | 完整的私钥（包括 `-----BEGIN` 和 `-----END`） |
| `DEPLOY_PORT` | SSH端口（可选） | `22`（默认）或 `2222` |

#### 生成 SSH 密钥对（如果还没有）

```bash
# 在本地生成密钥对
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/github_actions.pub user@your-server

# 复制私钥内容（用于 GitHub Secrets）
cat ~/.ssh/github_actions
```

### 方式2: Docker 部署

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `DOCKER_USERNAME` | Docker Hub 用户名 | `your-username` |
| `DOCKER_PASSWORD` | Docker Hub 密码或访问令牌 | `your-password` 或 `dckr_pat_xxx` |
| `DOCKER_REGISTRY` | 容器注册表地址（可选） | `docker.io`（默认）或 `registry.example.com` |

#### 获取 Docker Hub 访问令牌

1. 登录 [Docker Hub](https://hub.docker.com/)
2. 进入 **Account Settings** > **Security**
3. 点击 **New Access Token**
4. 复制生成的令牌作为 `DOCKER_PASSWORD`

## 服务器环境变量配置

**重要**：API 密钥应该在部署服务器上配置，而不是在 GitHub Secrets 中。

### 在服务器上创建 `.env` 文件

```bash
# 在服务器上创建 .env 文件
nano /path/to/smartvision/.env
```

内容示例：
```env
MODEL_TYPE=qwen
QWEN_API_KEY=your-real-api-key-here
MOONDREAM_API_KEY=your-real-api-key-here
OPENAI_API_KEY=your-openai-key-if-needed
CLAUDE_API_KEY=your-claude-key-if-needed
GEMINI_API_KEY=your-gemini-key-if-needed
FFMPEG_PATH=/usr/bin/ffmpeg
SMARTVISION_TEMP_DIR=/tmp/smartvision
```

### 或使用系统环境变量

```bash
# 在 /etc/environment 或 ~/.bashrc 中添加
export MODEL_TYPE=qwen
export QWEN_API_KEY=your-real-api-key-here
export MOONDREAM_API_KEY=your-real-api-key-here
```

## 部署方式

### 方式1: 使用 Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/smartvision.git
cd smartvision

# 2. 创建 .env 文件
cp .env.example .env
nano .env  # 编辑并填入真实API密钥

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 方式2: 直接部署（不使用 Docker）

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/smartvision.git
cd smartvision

# 2. 安装 Python 依赖
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 安装前端依赖并构建
cd frontend
npm install
npm run build
cd ..

# 4. 配置环境变量
cp .env.example .env
nano .env  # 编辑并填入真实API密钥

# 5. 启动服务
python backend_api.py
```

### 方式3: 使用 systemd 服务（Linux）

创建服务文件 `/etc/systemd/system/smartvision.service`:

```ini
[Unit]
Description=SmartVision Video Processing Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/smartvision
EnvironmentFile=/path/to/smartvision/.env
ExecStart=/usr/bin/python3 /path/to/smartvision/backend_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartvision
sudo systemctl start smartvision
sudo systemctl status smartvision
```

## CI/CD 工作流说明

### 工作流触发条件

- **Push 到 main/master 分支**：自动运行完整 CI/CD 流程
- **Pull Request**：只运行代码检查和测试
- **手动触发**：在 GitHub Actions 页面可以手动运行

### 工作流步骤

1. **Lint and Test**: 代码质量检查
2. **Build Frontend**: 构建前端生产版本
3. **Deploy**: 部署到服务器（仅 main/master 分支）
4. **Docker Build**: 构建并推送 Docker 镜像（仅 main/master 分支）

## 安全最佳实践

1. ✅ **使用 GitHub Secrets** 存储部署凭证（SSH密钥、Docker密码）
2. ✅ **在服务器上配置 API 密钥**（通过 .env 文件或环境变量）
3. ✅ **定期轮换密钥**
4. ✅ **使用最小权限原则**（SSH 用户只拥有必要权限）
5. ✅ **启用防火墙**（只开放必要端口）
6. ✅ **使用 HTTPS**（如果部署到公网）
7. ✅ **定期更新依赖**（修复安全漏洞）

## 故障排查

### CI/CD 失败

1. 检查 GitHub Actions 日志
2. 确认所有必需的 Secrets 都已配置
3. 检查服务器连接（SSH 密钥、端口等）
4. 验证服务器上的环境变量配置

### 部署后服务无法启动

1. 检查服务器日志：`docker-compose logs` 或 `journalctl -u smartvision`
2. 验证环境变量是否正确加载
3. 检查端口是否被占用：`netstat -tulpn | grep 5000`
4. 验证 API 密钥是否有效

## 监控和维护

### 健康检查

服务提供健康检查接口：`GET /api/health`

### 日志查看

```bash
# Docker
docker-compose logs -f smartvision

# systemd
journalctl -u smartvision -f

# 直接运行
python backend_api.py  # 日志输出到控制台
```








