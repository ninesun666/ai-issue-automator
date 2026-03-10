# Issue Automator - GitHub Issue 自动化处理工具

一套完整的 GitHub Issue 自动化处理方案，支持 Webhook 触发、AI 分析、自动创建分支和 PR。

---

## 核心特性

- **Webhook 触发** - 接收 GitHub Webhook，自动响应 Issue 创建
- **AI 分析需求** - 使用 iFlow CLI 分析 Issue 并拆解任务
- **自动创建分支** - 根据 Issue 类型创建 feat/fix 分支
- **代码自动生成** - AI 自动实现功能代码
- **PR 自动创建** - 完成后自动创建 Pull Request
- **通知人工评审** - 在 Issue 中评论 PR 链接

---

## 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/issue-automator.git
cd issue-automator

# 安装依赖
pip install -e .
```

### 2. 配置

创建 `.env` 文件：

```bash
# GitHub Personal Access Token
GITHUB_TOKEN=ghp_your_token_here

# Webhook 密钥
GITHUB_WEBHOOK_SECRET=your_secret_here

# 服务端口 (可选)
WEBHOOK_PORT=8080
```

### 3. 启动服务

```bash
# 启动 webhook 服务
issue-automator automation start

# 或使用短命令
ia automation start
```

### 4. 配置 GitHub Webhook

在 GitHub 仓库设置中：

1. 进入 **Settings** → **Webhooks** → **Add webhook**
2. 填写配置：
   - **Payload URL**: `http://your-server:8080/webhook`
   - **Content type**: `application/json`
   - **Secret**: 与 `.env` 中 `GITHUB_WEBHOOK_SECRET` 一致
   - **Events**: 选择 `Issues`

---

## 工作流程

```
GitHub Issue 创建
       │
       ▼
  Webhook 触发
       │
       ▼
  AI 分析需求
       │
       ▼
  创建分支 (feat/issue-xxx)
       │
       ▼
  生成代码
       │
       ▼
  创建 Pull Request
       │
       ▼
  通知人工评审
```

---

## 项目结构

```
issue-automator/
├── issue_automator/           # 核心代码
│   ├── cli/                   # 命令行接口
│   ├── config/                # 配置管理
│   ├── core/                  # 核心调度
│   ├── analyzer/              # Issue 分析
│   ├── git_manager/           # Git 操作
│   ├── notification/          # GitHub 通知
│   ├── webhook/               # Webhook 服务
│   └── providers/             # AI 提供者
├── tests/                     # 测试文件
├── templates/                 # 模板文件
├── Dockerfile
├── docker-compose.yml
└── setup.py
```

---

## Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f issue-automator
```

---

## 命令行

```bash
# 启动自动化服务
issue-automator automation start

# 指定端口
issue-automator automation start --port 9000

# 指定工作目录
issue-automator automation start --work-dir /path/to/repos

# 使用配置文件
issue-automator automation start -c config.json
```

---

## 配置文件

`issue-automator.config.json`:

```json
{
  "webhook": {
    "port": 8080,
    "host": "0.0.0.0",
    "secret": "your-webhook-secret"
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

## 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | ✓ |
| `GITHUB_WEBHOOK_SECRET` | Webhook 签名密钥 | ✓ |
| `WEBHOOK_PORT` | 服务端口 | 默认 8080 |
| `WEBHOOK_HOST` | 监听地址 | 默认 0.0.0.0 |

---

## GitHub Token 权限

需要的权限：
- `repo` - 完整仓库访问
- `write:discussion` - 讨论写入

---

## 许可证

MIT License