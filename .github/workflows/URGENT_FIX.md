# 🚨 紧急修复：Docker Hub认证问题

## 问题诊断
错误信息显示"Username and password required"，说明GitHub Secrets没有正确配置。

## 立即解决方案

### 1. 手动检查GitHub Secrets
访问：https://github.com/akita-dot/smartvision/settings/secrets/actions

**必须确保以下两个Secrets存在：**
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

### 2. 如果Secrets不存在，立即创建：

#### 创建DOCKERHUB_USERNAME：
1. 点击"New repository secret"
2. Name: `DOCKERHUB_USERNAME`
3. Secret: `akita514` （你的Docker Hub用户名）

#### 创建DOCKERHUB_TOKEN：
1. 登录Docker Hub：https://hub.docker.com/
2. 头像 → Account Settings → Security
3. 点击"New Access Token"
4. Description: `GitHub Actions`
5. Permissions: 选择 **Read, Write, Delete**
6. 复制生成的token
7. 在GitHub中创建secret：
   - Name: `DOCKERHUB_TOKEN`
   - Secret: 粘贴刚才的token

### 3. 验证配置
创建完成后，触发新的构建：
```bash
git commit --allow-empty -m "Test Docker Hub secrets"
git push origin main
```

### 4. 检查Actions日志
访问：https://github.com/akita-dot/smartvision/actions
查看"Debug - Check secrets"步骤的输出。

## 常见错误
- ❌ 使用密码而不是Access Token
- ❌ Access Token权限不足
- ❌ Secret名称拼写错误
- ❌ 没有保存Secret

## 快速检查清单
- [ ] DOCKERHUB_USERNAME secret存在
- [ ] DOCKERHUB_TOKEN secret存在
- [ ] Token具有完整权限
- [ ] 用户名正确（不是邮箱）
- [ ] 查看Actions日志确认

**如果问题仍然存在，请检查Actions日志中的"Debug - Check secrets"步骤输出。**