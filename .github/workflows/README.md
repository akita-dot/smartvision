# CI/CD 工作流说明

## 工作流概述

这个 CI/CD 工作流在 GitHub Actions 的临时虚拟机上运行，用于：
- ✅ 代码质量检查
- ✅ 语法验证
- ✅ 前端构建测试
- ✅ Docker 镜像构建测试

**注意**：此工作流不包含部署步骤，只进行测试和构建验证。

## 触发条件

- **Push 到 main/master/develop 分支**：自动运行完整流程
- **Pull Request**：运行代码检查和测试
- **手动触发**：在 GitHub Actions 页面可以手动运行

## 工作流步骤

### 1. Lint and Test
- 检查 Python 代码语法
- 运行代码质量检查（flake8）
- 验证前端依赖安装
- 检查前端构建

### 2. Build Frontend
- 安装前端依赖
- 构建前端生产版本
- 保存构建产物（保留1天）

### 3. Test Docker Build
- 构建 Docker 镜像（仅测试，不推送）
- 验证 Dockerfile 配置正确性
- 使用 GitHub Actions 缓存加速构建

## 环境变量

工作流使用以下环境变量（在 GitHub Actions 临时虚拟机上）：
- `PYTHON_VERSION`: Python 版本（3.10）
- `NODE_VERSION`: Node.js 版本（18）

## 本地测试

### 运行代码检查

```bash
# Python 代码检查
pip install flake8
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 前端构建测试
cd frontend
npm install
npm run build
```

### 测试 Docker 构建

```bash
# 构建 Docker 镜像
docker build -t smartvision:test .
```

## 注意事项

1. **API 密钥**：工作流中不需要配置 API 密钥，因为只进行构建测试
2. **构建产物**：前端构建产物会保存1天，可用于后续下载
3. **Docker 镜像**：只构建不推送，用于验证 Dockerfile 配置
4. **临时虚拟机**：每次运行都在全新的虚拟机上，运行完成后自动清理

## 故障排查

### 工作流失败

1. 查看 GitHub Actions 日志
2. 检查代码语法错误
3. 验证依赖安装是否成功
4. 确认 Dockerfile 配置正确

### 本地复现问题

```bash
# 在本地运行相同的检查
python -m py_compile backend_api.py model_manager.py config.py
cd frontend && npm ci && npm run build
docker build -t smartvision:test .
```
