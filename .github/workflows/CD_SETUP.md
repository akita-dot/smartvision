# CI/CD 部署配置指南

## SSH 部署配置

### 1. 配置 GitHub Secrets

在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加以下 secrets：

```
SERVER_HOST=你的服务器IP地址
SERVER_USERNAME=服务器用户名
SERVER_SSH_KEY=SSH私钥内容
SERVER_PORT=SSH端口（可选，默认22）
```

### 2. 生成 SSH 密钥对

在本地生成 SSH 密钥：

```bash
# 生成密钥对
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions

# 查看公钥内容
cat ~/.ssh/github_actions.pub
```

### 3. 配置服务器

将公钥添加到服务器的 authorized_keys：

```bash
# 在服务器上执行
mkdir -p ~/.ssh
echo "你的公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### 4. 部署脚本说明

SSH 部署步骤：
1. 拉取最新 Docker 镜像
2. 停止并删除旧容器
3. 启动新容器
4. 清理无用镜像

### 5. 故障排除

#### 错误：missing server host
**原因**：未配置 SERVER_HOST secret
**解决**：在 GitHub Secrets 中添加 SERVER_HOST

#### 错误：permission denied
**原因**：SSH 密钥配置错误
**解决**：检查私钥格式和服务器上的公钥配置

#### 错误：connection timeout
**原因**：网络连接问题或防火墙阻止
**解决**：检查服务器防火墙设置和 SSH 端口

#### 错误：自托管 runner 不拾取任务
**原因**：标签不匹配或 runner 未正确配置
**解决**：
1. 检查 workflow 中的 `runs-on` 标签是否完整
2. 确认 runner 配置时添加了对应的标签
3. 在 GitHub Settings > Actions > Runners 中验证 runner 状态和标签

## 自托管 Runner 部署（推荐）

### 优势
- 无需暴露 SSH 端口
- 更安全的部署方式
- 更快的部署速度

### 配置步骤

1. 在服务器上安装 GitHub Actions Runner
2. 注册 runner 到仓库
3. 确保 runner 有 Docker 权限

### Runner 安装命令

#### Windows 系统

```powershell
# 下载 runner
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-win-x64-2.311.0.zip -OutFile actions-runner.zip

# 解压
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("actions-runner.zip", "$PWD")

# 配置（添加自定义标签）
.\config.cmd --url https://github.com/你的用户名/你的仓库名 --token 你的token --labels Windows,X64,self-hosted

# 运行
.\run.cmd
```

#### Linux 系统

```bash
# 下载 runner
wget https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# 解压
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# 配置（添加自定义标签）
./config.sh --url https://github.com/你的用户名/你的仓库名 --token 你的token --labels Linux,X64,self-hosted

# 运行
./run.sh
```

### 重要：标签配置说明

**问题**：如果仅使用 `self-hosted` 标签，可能因标签不完整导致无法匹配任务。

**解决方案**：
1. 在配置 runner 时添加完整标签：`--labels Windows,X64,self-hosted`
2. 在 workflow 中使用完整标签：`runs-on: [self-hosted, Windows, X64]`
3. 确保 runner 标签与 workflow 中的标签完全匹配

### 验证 Runner 标签

```powershell
# Windows 查看 runner 状态
.\config.cmd list

# 或在 GitHub 仓库 Settings > Actions > Runners 中查看标签
```

## 部署验证

部署完成后，可以通过以下方式验证：

```bash
# 检查容器状态
docker ps | grep smartvision-app

# 检查服务健康状态
curl http://localhost:5000/health

# 查看容器日志
docker logs smartvision-app
```