# 命理运势系统

## 快速启动

```bash
# 后端（端口 8080）
cd E:\fortune\server
E:\conda_envs\fortune\python.exe -m uvicorn app.main:app --port 8080

# 前端（端口 3000）
cd E:\fortune\client
npm run dev
```

## 关键路径

| 路径 | 说明 |
|------|------|
| `server/app/api/v1/` | 后端 API 路由 |
| `server/app/models/` | SQLAlchemy 数据模型 |
| `server/fortune_engine/` | 命理计算引擎（八字/六爻/奇门） |
| `server/fortune_engine/services/deepseek.py` | LLM 解读服务 |
| `client/src/features/` | 前端功能模块 |
| `docs/specs/` | 30 个功能 Spec |
| `STARTUP.md` | 完整启动指南 |

## LLM 配置

- 供应商：Xiaomi MiMo（OpenAI 兼容格式）
- API URL：`https://token-plan-cn.xiaomimimo.com/v1`
- 模型：`mimo-v2.5`
- 配置层级：用户个人中心 > `.env` 服务器默认
- 模型名含 `[1M]` 等标注时会自动清理

## 注意事项

- 后端端口用 8080（避免 Windows 端口权限问题）
- Python 必须用 `E:\conda_envs\fortune\python.exe` 完整路径
- API Key 脱敏显示（含 `***`），保存时自动跳过脱敏值
- 前端 regenerate 接口超时 60 秒（LLM 调用耗时较长）
