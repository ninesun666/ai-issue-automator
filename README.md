# Issue Automator - GitHub Issue 自动化处理工具

一套完整的 GitHub Issue 自动化处理方案，支持 Webhook 触发、AI 分析、自动创建分支和 PR。

## 目录

- [快速开始](#快速开始)
- [详细安装](#详细安装)
- [配置指南](#配置指南)
- [GitHub 配置](#github-配置)
- [运行服务](#运行服务)
- [Docker 部署](#docker-部署)
- [故障排除](#故障排除)

---

## 快速开始

### 前置要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 运行服务 |
| Git | 2.x | 仓库操作 |
| iFlow CLI | latest | AI 分析（可选） |

### 一键安装

**Windows:**
```cmd
quick-start.bat
```

**Linux/macOS:**
```bash
chmod +x quick-start.sh
./quick-start.sh
```

---

## 详细安装

### 1. 克隆仓库

```bash
git clone https://github.com/ninesun666/ai-issue-automator.git
cd ai-issue-automator
```

### 2. 安装依赖

```bash
# 方式1: pip 安装（推荐）
pip install -e .

# 方式2: 使用 requirements
pip install -r requirements.txt
```

### 3. 验证安装

```bash
# 检查命令是否可用
issue-automator --help
ia --help
```

---

## 配置指南

### 1. 创建 GitHub Token

1. 打开 GitHub → **Settings** → **Developer settings**
2. 点击 **Personal access tokens** → **Tokens (classic)**
3. 点击 **Generate new token (classic)**
4. 设置：
   - Note: `issue-automator`
   - Expiration: 选择有效期
   - 权限勾选：
     - ✅ `repo` (完整仓库访问)
     - ✅ `write:discussion`
5. 点击 **Generate token**
6. **立即复制保存**（只显示一次）

### 2. 创建 Webhook Secret

生成一个随机字符串作为 Webhook 密钥：

```bash
# Linux/macOS
openssl rand -hex 32

# Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

### 3. 配置 .env 文件

复制模板并编辑：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# GitHub Personal Access Token (必需)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Webhook 签名密钥 (必需)
GITHUB_WEBHOOK_SECRET=your_random_secret_here

# 服务配置 (可选)
WEBHOOK_PORT=8080
WEBHOOK_HOST=0.0.0.0
```

### 4. 配置文件（可选）

创建 `issue-automator.config.json`：

```json
{
  "webhook": {
    "port": 8080,
    "host": "0.0.0.0",
    "secret": "${GITHUB_WEBHOOK_SECRET}"
  },
  "github": {
    "token": "${GITHUB_TOKEN}",
    "api_base": "https://api.github.com"
  },
  "workflow": {
    "auto_merge": false,
    "require_review": true,
    "max_retry": 3
  }
}
```

---

## GitHub 配置

### 配置 Webhook

1. 打开目标 GitHub 仓库
2. 进入 **Settings** → **Webhooks** → **Add webhook**
3. 填写配置：

| 字段 | 值 | 说明 |
|------|-----|------|
| **Payload URL** | `http://your-server:8080/webhook` | 服务器地址 |
| **Content type** | `application/json` | 数据格式 |
| **Secret** | 与 `.env` 中 `GITHUB_WEBHOOK_SECRET` 相同 | 签名验证 |
| **SSL verification** | 启用（生产环境） | 安全验证 |
| **Which events** | 选择 `Issues` | 触发事件 |
| **Active** | ✅ 勾选 | 启用 |

4. 点击 **Add webhook**

### 本地测试（内网穿透）

GitHub 无法直接访问本地服务器，需要内网穿透：

```bash
# 方式1: ngrok
ngrok http 8080
# 使用 https://xxx.ngrok.io/webhook 作为 Payload URL

# 方式2: cloudflared
cloudflared tunnel --url http://localhost:8080
```

---

## 运行服务

### 命令行启动

```bash
# 基本启动
issue-automator automation start

# 短命令
ia automation start

# 指定端口
ia automation start --port 9000

# 指定配置文件
ia automation start -c config.json

# 指定工作目录
ia automation start --work-dir /path/to/repos
```

### 后台运行

**Linux/macOS:**
```bash
nohup issue-automator automation start > logs/automator.log 2>&1 &
```

**Windows:**
```cmd
start /B issue-automator automation start > logs\automator.log 2>&1
```

### 验证服务

```bash
# 健康检查
curl http://localhost:8080/health

# 预期响应
{"status": "healthy", "service": "issue-automator"}
```

---

## Docker 部署

### 快速启动

```bash
# 创建 .env 文件
cp .env.example .env
# 编辑 .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f issue-automator
```

### 自定义配置

```bash
# 自定义端口
WEBHOOK_PORT=9000 docker-compose up -d

# 构建时指定端口
docker-compose build --build-arg WEBHOOK_PORT=9000
```

### 生产部署

```bash
# 使用 nginx 反向代理
docker-compose --profile production up -d
```

---

## 故障排除

### 常见问题

#### 1. Token 权限不足

**错误**: `403 Resource not accessible by personal access token`

**解决**: 确保 Token 有以下权限：
- `repo`
- `write:discussion`

#### 2. Webhook 签名验证失败

**错误**: `401 Invalid signature`

**解决**:
- 检查 `.env` 中的 `GITHUB_WEBHOOK_SECRET`
- 确保 GitHub Webhook 配置的 Secret 与之一致

#### 3. 无法创建分支

**错误**: `Failed to create branch`

**解决**:
- 检查 Token 是否有 `repo` 权限
- 检查仓库是否存在
- 检查分支名是否已存在

#### 4. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :8080

# Linux/macOS
lsof -i :8080

# 使用其他端口
WEBHOOK_PORT=9000 issue-automator automation start
```

#### 5. 本地无法接收 Webhook

**原因**: GitHub 无法访问本地服务器

**解决**: 使用内网穿透工具（ngrok、cloudflared）

---

## 环境变量参考

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `GITHUB_TOKEN` | ✅ | - | GitHub Personal Access Token |
| `GITHUB_WEBHOOK_SECRET` | ✅ | - | Webhook 签名密钥 |
| `WEBHOOK_PORT` | ❌ | 8080 | 服务端口 |
| `WEBHOOK_HOST` | ❌ | 0.0.0.0 | 监听地址 |

---

## 项目结构

```
issue-automator/
├── issue_automator/       # 核心代码
│   ├── cli/              # 命令行接口
│   ├── config/           # 配置管理
│   ├── core/             # 核心调度
│   ├── analyzer/         # Issue 分析
│   ├── git_manager/      # Git 操作
│   ├── notification/     # GitHub 通知
│   └── webhook/          # Webhook 服务
├── tests/                # 测试文件
├── templates/            # 模板文件
├── quick-start.bat       # Windows 快速启动
├── quick-start.sh        # Linux/macOS 快速启动
├── Dockerfile
├── docker-compose.yml
└── setup.py
```

---

## 许可证

MIT License
