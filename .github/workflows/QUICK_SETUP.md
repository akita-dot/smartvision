# SmartVision 快速配置指南

## 🚀 立即配置 Docker Hub

### 方法一：通过 GitHub 网页界面配置

1. **打开仓库设置**
   - 进入你的 GitHub 仓库
   - 点击 Settings 标签页
   - 在左侧菜单中选择 "Secrets and variables" → "Actions"

2. **添加 Docker Hub Secrets**
   
   **添加 DOCKERHUB_USERNAME：**
   - 点击 "New repository secret"
   - Name: `DOCKERHUB_USERNAME`
   - Secret: `你的Docker Hub用户名`
   - 点击 "Add secret"

   **添加 DOCKERHUB_TOKEN：**
   - 点击 "New repository secret"  
   - Name: `DOCKERHUB_TOKEN`
   - Secret: `你的Docker Hub访问令牌`
   - 点击 "Add secret"

### 方法二：使用 GitHub CLI（推荐）

如果你已安装 GitHub CLI：

```bash
# 设置 Docker Hub 用户名
gh secret set DOCKERHUB_USERNAME --body "你的Docker Hub用户名"

# 设置 Docker Hub Token
gh secret set DOCKERHUB_TOKEN --body "你的Docker Hub访问令牌"
```

## ✅ 验证配置

配置完成后，你可以：

1. **手动触发工作流**：
   - 进入仓库的 Actions 页面
   - 选择 "Deploy and Build" 工作流
   - 点击 "Run workflow"

2. **检查构建状态**：
   - 观察 Docker 构建步骤是否成功
   - 确认镜像是否推送到 Docker Hub

## 🔍 常见问题

### Token 权限问题
如果遇到权限错误，请确保：
- Token 是在 Docker Hub 的 "Security" 页面创建的 Access Token
- Token 包含 "Read, Write, Delete" 权限

### 用户名错误
- 使用 Docker Hub 用户名，不是邮箱地址
- 用户名区分大小写

## 📞 需要帮助？

如果配置过程中遇到问题：
1. 检查 Secrets 是否正确添加
2. 确认 Token 没有过期
3. 查看工作流日志获取详细错误信息

---

**配置完成后，你的 SmartVision 项目将能够自动构建和推送 Docker 镜像！** 🎉