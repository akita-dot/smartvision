# GitHub Actions CI/CD 使用指南

## 快速开始

### 1. 提交代码到 GitHub

工作流会在以下情况自动触发：

```bash
# 提交代码到 main/master/develop 分支
git add .
git commit -m "Your commit message"
git push origin main
```

### 2. 查看工作流运行

1. 打开你的 GitHub 仓库
2. 点击 **Actions** 标签页
3. 查看工作流运行状态

## 工作流说明

### 自动触发条件

- ✅ **Push 到 main/master/develop 分支**：运行完整测试和构建
- ✅ **Pull Request**：运行代码检查和测试
- ✅ **手动触发**：在 Actions 页面可以手动运行

### 工作流步骤

#### 1. Lint and Test（代码质量检查）

在临时虚拟机上运行：
- ✅ 检查 Python 代码语法
- ✅ 运行代码质量检查（flake8）
- ✅ 安装前端依赖
- ✅ 验证前端构建

#### 2. Build Frontend（构建前端）

在临时虚拟机上运行：
- ✅ 安装前端依赖
- ✅ 构建前端生产版本
- ✅ 保存构建产物（保留1天）

#### 3. Test Docker Build（Docker 构建测试）

在临时虚拟机上运行：
- ✅ 构建 Docker 镜像（仅测试，不推送）
- ✅ 验证 Dockerfile 配置正确性

## 手动触发工作流

### 方法1：通过 GitHub 网页

1. 打开 GitHub 仓库
2. 点击 **Actions** 标签页
3. 在左侧选择 **CI/CD Pipeline
4. 点击右上角 **Run workflow** 按钮
5. 选择分支，点击 **Run workflow**

### 方法2：通过 GitHub CLI

```bash
# 安装 GitHub CLI（如果还没有）
# Windows: winget install GitHub.cli
# Mac: brew install gh
# Linux: 参考 https://cli.github.com/

# 登录
gh auth login

# 手动触发工作流
gh workflow run deploy.yaml
```

## 查看工作流结果

### 查看运行日志

1. 进入 **Actions** 标签页
2. 点击左侧的工作流运行记录
3. 点击具体的 Job（如 "Lint and Test"）
4. 查看每个步骤的详细日志

### 下载构建产物

1. 在工作流运行页面
2. 找到 **Build Frontend** job
3. 在右侧 **Artifacts** 部分下载 `frontend-dist`

## 工作流状态说明

- ✅ **绿色勾号**：所有步骤成功
- ❌ **红色叉号**：某个步骤失败
- 🟡 **黄色圆点**：正在运行中
- ⚠️ **橙色警告**：有警告但未失败

## 常见问题

### Q: 工作流失败了怎么办？

1. **查看日志**：点击失败的步骤查看详细错误信息
2. **检查代码**：确保代码语法正确
3. **检查依赖**：确保 `requirements.txt` 和 `package.json` 正确

### Q: 如何修复代码检查错误？

```bash
# 在本地运行相同的检查
pip install flake8
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 修复错误后重新提交
git add .
git commit -m "Fix linting errors"
git push
```

### Q: 工作流运行需要多长时间？

- **Lint and Test**: 约 2-5 分钟
- **Build Frontend**: 约 1-3 分钟
- **Test Docker Build**: 约 3-8 分钟
- **总计**: 约 6-16 分钟

### Q: 临时虚拟机会保留多久？

- 工作流运行完成后，临时虚拟机会立即被销毁
- 构建产物会保留 1 天，之后自动删除

## 本地测试（在提交前）

### 测试 Python 代码

```bash
# 安装依赖
pip install flake8 pytest
pip install -r requirements.txt

# 检查语法
python -m py_compile backend_api.py model_manager.py config.py

# 代码质量检查
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### 测试前端构建

```bash
cd frontend
npm install
npm run build
```

### 测试 Docker 构建

```bash
docker build -t smartvision:test .
```

## 工作流配置

工作流文件位置：`.github/workflows/deploy.yaml`

### 修改 Python 版本

编辑 `deploy.yaml` 文件中的：
```yaml
env:
  PYTHON_VERSION: '3.10'  # 修改为你需要的版本
```

### 修改 Node.js 版本

编辑 `deploy.yaml` 文件中的：
```yaml
env:
  NODE_VERSION: '18'  # 修改为你需要的版本
```

## 注意事项

1. **无需配置 Secrets**：此工作流不需要任何 GitHub Secrets
2. **无需 API 密钥**：只进行构建测试，不需要真实的 API 密钥
3. **临时环境**：每次运行都在全新的虚拟机上
4. **自动清理**：运行完成后自动清理所有文件

## 下一步

- ✅ 代码推送到 GitHub 后，工作流会自动运行
- ✅ 查看 Actions 标签页了解运行状态
- ✅ 修复任何错误后重新提交

