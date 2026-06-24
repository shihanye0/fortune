# 命理运势系统

## 快速启动（本地开发）

```bash
# 后端（端口 8080）
cd E:\fortune\server
E:\conda_envs\fortune\python.exe -m uvicorn app.main:app --port 8080

# 前端（端口 3000）
cd E:\fortune\client
npm run dev
```

## 生产环境

| 项目 | 值 |
|------|------|
| 服务器 | 腾讯云 Ubuntu 2核2G |
| IP | 82.157.186.52 |
| 访问 | http://82.157.186.52 |
| 后端 | systemd `fortune.service`，端口 8080 |
| 前端 | Nginx 静态文件 + 反向代理 |
| 数据库 | SQLite `/opt/fortune/server/fortune.db` |
| 更新 | `cd /opt/fortune && bash update.sh` |
| 克隆镜像 | `git clone --depth 1 https://gitclone.com/github.com/shihanye0/fortune.git` |

## 关键路径

| 路径 | 说明 |
|------|------|
| `server/app/api/v1/` | 后端 API 路由 |
| `server/app/models/` | SQLAlchemy 数据模型 |
| `server/fortune_engine/` | 命理计算引擎（八字/六爻/奇门） |
| `server/fortune_engine/services/deepseek.py` | LLM 解读服务 |
| `client/src/features/` | 前端功能模块 |
| `docs/specs/` | 30 个功能 Spec |
| `deploy.sh` / `update.sh` | 部署和更新脚本 |

## LLM 配置

- 供应商：Xiaomi MiMo（OpenAI 兼容格式）
- API URL：`https://token-plan-cn.xiaomimimo.com/v1`（不是 `/anthropic`）
- 模型：`mimo-v2.5`（去掉 `[1M]` 等标注）
- 配置层级：用户个人中心 > `.env` 服务器默认
- 测试连接接口：`POST /api/v1/users/me/llm-test`

## 推送配置

- SMTP 发件人：`3221275248@qq.com`
- 收件人：用户注册邮箱
- 推送内容：综合运势 + 四维评分 + 运势解读 + 12 时辰运势 + 概率事件
- 触发方式：GitHub Actions 每小时调用 `/api/v1/internal/daily-push`

## 注意事项

- 后端端口用 8080（避免 Windows 端口权限问题）
- Python 必须用 `E:\conda_envs\fortune\python.exe` 完整路径
- API Key 脱敏显示（含 `***`），保存时自动跳过脱敏值
- 前端 regenerate 接口超时 60 秒（LLM 调用耗时较长）
- 前端 `baseURL` 为空字符串（通过 Nginx 代理 `/api/`）
- 国内服务器克隆用 `gitclone.com` 镜像
