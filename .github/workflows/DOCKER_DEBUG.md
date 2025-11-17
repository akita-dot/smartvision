# Docker Hub 权限问题深度调试指南

## 🔍 问题诊断

如果按照标准步骤仍然出现权限不足，请按以下顺序排查：

## 1. Docker Hub 账户状态检查

### 检查账户类型
- 登录 [Docker Hub](https://hub.docker.com/)
- 检查是否为免费账户（有推送限制）
- 检查是否有未支付的账单

### 检查仓库权限
- 确认 `akita514/smartvision` 仓库存在
- 确认你有该仓库的写入权限
- 如果仓库不存在，先在Docker Hub创建

## 2. Token 创建详细步骤

### 创建新的 Personal Access Token
1. 登录 Docker Hub
2. 点击右上角头像 → **Account Settings**
3. 选择 **Security** 标签
4. 点击 **New Access Token**
5. 填写：
   - **Token name**: `github-actions-smartvision`
   - **Description**: `For GitHub Actions CI/CD`
   - **Permissions**: ✅ **Read, Write, Delete**
6. 点击 **Generate**
7. **立即复制Token**（只显示一次）

## 3. GitHub Secrets 配置验证

### 检查 Secrets 配置
1. 进入GitHub仓库
2. **Settings** → **Secrets and variables** → **Actions**
3. 确认以下Secrets：
   - `DOCKERHUB_USERNAME`: `akita514`
   - `DOCKERHUB_TOKEN`: 刚创建的完整Token

### 测试 Secrets
在GitHub Actions中添加调试步骤：
```yaml
- name: Debug Secrets
  run: |
    echo "Username length: ${{ secrets.DOCKERHUB_USERNAME }}"
    echo "Token length: ${{ secrets.DOCKERHUB_TOKEN }}"
```

## 4. 替代解决方案

### 方案A: 使用Docker CLI直接认证
```yaml
- name: Manual Docker Login
  run: |
    echo "${{ secrets.DOCKERHUB_TOKEN }}" | docker login -u "${{ secrets.DOCKERHUB_USERNAME }}" --password-stdin
```

### 方案B: 使用环境变量
```yaml
- name: Set Docker Credentials
  run: |
    echo "DOCKER_USERNAME=${{ secrets.DOCKERHUB_USERNAME }}" >> $GITHUB_ENV
    echo "DOCKER_TOKEN=${{ secrets.DOCKERHUB_TOKEN }}" >> $GITHUB_ENV
```

### 方案C: 分步构建和推送
```yaml
- name: Build only
  run: docker build -t akita514/smartvision:test .

- name: Push manually
  run: |
    echo "${{ secrets.DOCKERHUB_TOKEN }}" | docker login -u "${{ secrets.DOCKERHUB_USERNAME }}" --password-stdin
    docker push akita514/smartvision:test
```

## 5. 常见问题排查

### Token 格式问题
- 确保Token没有多余的空格或换行符
- 确保Token完整复制（通常很长）

### 用户名问题
- 使用Docker Hub用户名，不是邮箱
- 区分大小写

### 权限问题
- 免费账户有推送限制
- 确保账户状态正常

## 6. 紧急备用方案

如果Docker Hub持续有问题，可以：

### 使用GitHub Container Registry
```yaml
- name: Login to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

### 使用其他镜像仓库
- 阿里云容器镜像服务
- 腾讯云容器镜像服务
- AWS ECR

## 7. 联系支持

如果问题持续存在：
1. Docker Hub支持：support@docker.com
2. GitHub支持：github.com/support
3. 检查Docker Hub状态：status.docker.com

## 🚨 立即行动清单

1. [ ] 重新创建Docker Hub Token（确保ReadWriteDelete权限）
2. [ ] 更新GitHub Secrets中的DOCKERHUB_TOKEN
3. [ ] 确认DOCKERHUB_USERNAME为`akita514`
4. [ ] 在Docker Hub确认`akita514/smartvision`仓库存在
5. [ ] 重新触发GitHub Actions
6. [ ] 如果仍然失败，尝试手动Docker登录测试