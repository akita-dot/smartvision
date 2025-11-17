# Docker Hub 认证配置指南

## 🚨 重要：必须正确配置 GitHub Secrets

### 1. 检查当前配置
在 GitHub 仓库中：
1. 进入仓库设置页面
2. 点击 "Secrets and variables" → "Actions"
3. 检查以下 Secrets 是否存在且正确：

### 2. DOCKERHUB_USERNAME 配置
- **值**：你的 Docker Hub 用户名
- **示例**：`akita514`
- **注意**：使用用户名，不是邮箱地址

### 3. DOCKERHUB_TOKEN 配置（关键步骤）

#### 创建新的 Access Token：
1. 登录 [Docker Hub](https://hub.docker.com/)
2. 点击右上角头像 → "Account Settings"
3. 选择 "Security" 标签
4. 点击 "New Access Token"
5. 填写信息：
   - **Description**: `GitHub Actions CI/CD`
   - **Permissions**: 选择 **Read, Write, Delete**
6. 点击 "Generate"
7. **立即复制生成的 token**（只显示一次）

#### 在 GitHub 中配置：
1. 在仓库的 Secrets 页面点击 "New repository secret"
2. **Name**: `DOCKERHUB_TOKEN`
3. **Secret**: 粘贴刚才复制的 Access Token
4. 点击 "Add secret"

### 4. 验证配置
配置完成后，触发一次 GitHub Actions 来验证：
```bash
git commit --allow-empty -m "Test Docker Hub authentication"
git push origin main
```

### 5. 常见错误排查

#### 错误：unauthorized: incorrect username or password
**原因**：
- 使用了密码而不是 Access Token
- Access Token 权限不足
- 用户名错误

**解决**：
1. 重新创建具有完整权限的 Access Token
2. 确保使用 Docker Hub 用户名（不是邮箱）
3. 检查 token 是否正确复制

#### 错误：access token has insufficient scopes
**原因**：Access Token 权限不足

**解决**：
1. 删除现有 token
2. 创建新 token 时选择 "Read, Write, Delete" 权限
3. 更新 GitHub Secrets 中的 DOCKERHUB_TOKEN

### 6. 测试命令
本地测试 Docker Hub 连接：
```bash
docker login -u YOUR_USERNAME -p YOUR_TOKEN
docker pull alpine:latest
```

### 7. 安全提醒
- ⚠️ **永远不要**在代码中硬编码凭据
- ⚠️ **定期轮换** Access Token
- ⚠️ **限制权限**：只给予必要的权限

## 📋 配置检查清单

- [ ] DOCKERHUB_USERNAME 正确配置
- [ ] DOCKERHUB_TOKEN 使用 Access Token（不是密码）
- [ ] Access Token 具有 Read, Write, Delete 权限
- [ ] 用户名是 Docker Hub 用户名（不是邮箱）
- [ ] 已触发 GitHub Actions 测试
- [ ] 检查 Actions 日志确认认证成功

配置完成后，Docker 镜像将自动构建并推送到 Docker Hub。