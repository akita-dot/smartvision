# Docker Hub 权限问题解决方案

## 问题描述
```
ERROR: failed to build: failed to solve: failed to fetch oauth token: unexpected status from GET request to https://auth.docker.io/token?scope=repository%3A***%2Fsmartvision%3Apull%2Cpush&service=registry.docker.io: 401 Unauthorized: access token has insufficient scopes
```

## 解决方案

### 1. 检查 GitHub Secrets 配置

在 GitHub 仓库中确保正确配置了以下 Secrets：

1. 进入仓库设置页面
2. 点击 "Secrets and variables" → "Actions"
3. 检查以下 Secrets 是否存在且正确：

#### DOCKERHUB_USERNAME
- 你的 Docker Hub 用户名
- 例如：`akita514`

#### DOCKERHUB_TOKEN
- **重要**：使用 Access Token，不是密码
- 创建步骤：
  1. 登录 Docker Hub
  2. 点击右上角头像 → "Account Settings"
  3. 选择 "Security" 标签
  4. 点击 "New Access Token"
  5. 输入描述（如 "GitHub Actions"）
  6. 选择权限：**必须包含 "Read, Write, Delete" 权限**
  7. 复制生成的 token
- 创建步骤：
  1. 登录 Docker Hub
  2. 点击右上角头像 → "Account Settings"
  3. 选择 "Security" 标签
  4. 点击 "New Access Token"
  5. 输入描述（如 "GitHub Actions"）
  6. 选择权限：**必须包含 "Read, Write, Delete" 权限**
  7. 复制生成的 token

### 2. 常见问题排查

#### Token 权限不足
- 确保创建的 Access Token 包含写入权限
- 重新创建具有完整权限的 token

#### 用户名错误
- 确保使用 Docker Hub 用户名，不是邮箱
- 用户名区分大小写

#### 仓库权限
- 确保你有权限推送到目标仓库
- 如果是组织仓库，确保有相应权限

### 3. 临时解决方案

如果问题持续，可以暂时禁用 Docker 推送：

```yaml
# 在 docker-build-push job 中添加条件
if: github.ref == 'refs/heads/main' && false  # 暂时禁用
```

### 4. 验证步骤

1. 检查 Secrets 配置
2. 重新生成 Access Token
3. 确保仓库权限正确
4. 重新触发工作流

### 5. 替代方案

如果 Docker Hub 问题持续，可以考虑：

#### 使用 GitHub Container Registry
```yaml
- name: Log in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

#### 使用其他镜像仓库
- 阿里云容器镜像服务
- 腾讯云容器镜像服务
- AWS ECR

## 快速修复步骤

1. **立即检查**：确认 GitHub Secrets 中的 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN`
2. **重新创建 Token**：在 Docker Hub 创建新的 Access Token，确保包含完整权限
3. **更新 Secrets**：在 GitHub 中更新 `DOCKERHUB_TOKEN`
4. **重新运行**：手动触发工作流测试

## 联系支持

如果问题仍然存在：
- 检查 Docker Hub 账户状态
- 确认没有超出 API 限制
- 联系 Docker Hub 支持