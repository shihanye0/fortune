# 命理运势系统 - 启动指南

## 环境要求

| 环境 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | Conda 环境：`E:\conda_envs\fortune` |
| Node.js | 18+ | npm 包管理 |
| MySQL | 8.0+ | 生产环境数据库 |

## 快速启动

### 1. 启动后端（终端 1）

```bash
# 进入项目目录
cd E:\fortune\server

# 使用完整 conda 环境路径启动（端口 8080，避免 Windows 端口权限问题）
E:\conda_envs\fortune\python.exe -m uvicorn app.main:app --port 8080
```

### 2. 启动前端（终端 2）

```bash
# 进入前端目录
cd E:\fortune\client

# 启动开发服务器
npm run dev
```

## 访问地址

| 页面 | 地址 | 说明 |
|------|------|------|
| **首页** | http://localhost:3000 | 产品介绍 |
| **登录** | http://localhost:3000/login | 用户登录 |
| **注册** | http://localhost:3000/register | 用户注册 |
| **运势** | http://localhost:3000/fortune | 每日运势（需登录） |
| **占卜** | http://localhost:3000/divination | 六爻/奇门占卜（需登录） |
| **个人中心** | http://localhost:3000/profile | 个人信息管理（需登录） |
| **API 文档** | http://localhost:8080/docs | Swagger API 文档 |

## 测试流程

1. **首页** → 查看产品介绍和功能卡片
2. **注册** → 创建账号（用户名/邮箱/密码/生辰信息）
3. **登录** → 使用注册的账号登录
4. **个人中心** → 设置生辰信息（用于八字排盘）
5. **运势** → 查看今日运势和历史运势
6. **占卜** → 测试六爻占卜和奇门遁甲
7. **API 文档** → http://localhost:8000/docs 测试接口

## 运行测试

### 前端单元测试

```bash
cd E:\fortune\client
npm test
```

### 后端单元测试

```bash
cd E:\fortune\server
E:\conda_envs\fortune\python.exe -m pytest tests/ -v
```

### E2E 自动化测试

```bash
cd E:\fortune\client
npx playwright test
```

## 数据库配置

### 本地开发（SQLite）

默认使用 SQLite，无需额外配置。

### 生产环境（MySQL）

编辑 `server/.env` 文件：

```env
DATABASE_URL=mysql+pymysql://fortune:Fortune2026!@localhost:3306/fortune
```

初始化数据库：

```bash
cd E:\fortune\server
E:\conda_envs\fortune\python.exe scripts/init_db.py
E:\conda_envs\fortune\python.exe -m alembic upgrade head
```

## 常见问题

### 1. 端口被占用

```bash
# 查找占用端口的进程
netstat -ano | findstr :8080

# 强制结束进程
taskkill /F /PID <进程ID>
```

### 2. conda 环境激活失败

使用完整路径运行 Python：

```bash
E:\conda_envs\fortune\python.exe -m uvicorn app.main:app --port 8000
```

### 3. 前端页面空白

检查浏览器控制台（F12）是否有错误，通常是：
- 后端未启动
- API 代理配置错误
- 依赖未安装

### 4. 测试失败

```bash
# 前端测试
cd E:\fortune\client
npm test

# 后端测试
cd E:\fortune\server
E:\conda_envs\fortune\python.exe -m pytest tests/ -v
```

## 项目结构

```
E:\fortune\
├── client/                 # 前端 Vue 3 项目
│   ├── src/
│   │   ├── app/           # 应用入口、路由
│   │   ├── features/      # 功能模块
│   │   ├── shared/        # 共享组件和工具
│   │   └── test/          # 测试配置
│   ├── tests/e2e/         # E2E 测试
│   └── package.json
├── server/                 # 后端 FastAPI 项目
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── models/        # 数据模型
│   │   └── services/      # 业务逻辑
│   ├── fortune_engine/    # 命理计算引擎
│   ├── tests/             # 测试文件
│   └── requirements.txt
├── docs/                   # 文档
├── .github/workflows/      # GitHub Actions
└── README.md
```

## 技术栈

### 前端
- Vue 3 + TypeScript
- Vite 6
- Element Plus
- Pinia (状态管理)
- Vue Router
- Vitest (单元测试)
- Playwright (E2E 测试)

### 后端
- Python 3.10
- FastAPI
- SQLAlchemy + SQLite（开发）/ MySQL（生产）
- Alembic (数据库迁移)
- JWT 认证 + bcrypt
- Xiaomi MiMo API（LLM 解读）
- pytest (单元测试)

## 联系方式

- GitHub: https://github.com/shihanye0/fortune
