# 命理运势系统（fortune）

八字 + 紫微斗数 + 六爻 + 奇门遁甲的个人命理 Web 应用，含每日推送（邮件/飞书）与 AI 解读。

## 功能

- **每日运势**：八字排盘（lunar-python 精确节气口径）→ 四维评分（1-5 分制）→ DeepSeek 解读，十二时辰宜忌、概率事件、反馈闭环
- **紫微斗数**：十二宫命盘，安星诀 port 自 [iztro](https://github.com/SylarLong/iztro)（MIT），口径确认参照 [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu)（MIT），与 iztro 金标准 54/54 逐字段一致；真太阳时校正（可选，按出生城市经度+均时差）；流年四化落宫；AI 解读与历史反馈
- **六爻/奇门**：一事一测 + AI 解读
- **每日推送**：邮件（QQ SMTP）+ 飞书 + 纯文本三通道同一份简报——综合状态/四维/幸运信息/财神喜神方位/冲煞/节气横幅/八字大运/今日一卦（含 AI 解读）/紫微流日（日干四化+流年四化落本命宫+当前大限）/十二时辰全量/行动关注点全量/今日一问/周日周报
- **真太阳时**：个人中心选出生城市（内置 39 城经度表），紫微排盘按经度差+NOAA 均时差校正，口径注明
- **可追溯性**：每日运势落库带 `calculation_version`（`fortune_engine.ENGINE_VERSION`），算法升级不改写历史口径

## 技术栈

FastAPI + SQLAlchemy 2 + MySQL/SQLite · Vue 3 + TS + Element Plus + Pinia · DeepSeek（OpenAI 兼容）· systemd + Nginx（腾讯云）· GitHub Actions 每小时推送调度

## 快速开始

```bash
# 后端（Python 3.10+）
cd server && pip install -r requirements.txt
E:\conda_envs\fortune\python.exe -m uvicorn app.main:app --port 8080

# 前端
cd client && npm install && npm run dev   # http://localhost:3000
```

配置见 `server/.env.example`（DATABASE_URL / DEEPSEEK_API_KEY / SMTP / INTERNAL_API_KEY 等）。

## 测试

```bash
cd server && python -m pytest tests            # 228 用例（含 iztro 金标准 54 例）
cd client && npm test                          # vitest
cd client && npx playwright test               # e2e
cd server/scripts/ziwei-golden && node gen.mjs # 紫微金标准再生成（需 npm i iztro lunar-javascript）
```

## 部署

腾讯云 Ubuntu（82.157.186.52）：`git push` 后服务器 `bash update.sh`（拉代码/pip/npm build/sudo 重启）。
数据库变更走 alembic（幂等迁移），生产首次升级需手工执行对应 DDL（见 docs/specs）。

## 文档

- `STARTUP.md` 本地启动 · `docs/specs/` 31 个功能 spec · `docs/research/` 产品对标与优化决策
- 推送预览：`docs/preview/push-preview-<日期>.html`

## License 与致谢

本仓代码 MIT。紫微排盘算法源自 iztro（MIT）；排盘口径与词表参考 Renhuai123/ziwei-doushu（MIT）；
夏令时表与真太阳时算法移植自 Renhuai123（MIT）。未使用其禁商用内容（倪师原话 CC BY-NC-SA、解读数据集 CC BY 4.0 大文件未入库）。
