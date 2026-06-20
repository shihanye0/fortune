# 命理运势系统设计文档

> 创建日期：2026-06-20
> 状态：设计通过，待实施

## 一、项目概述

### 1.1 项目目标

构建一个基于中国传统命理学（生辰八字、周易六爻、奇门遁甲）的个性化运势推算系统。用户注册后填写生辰信息，系统每天自动推算运势并通过 QQ 邮箱 / 飞书推送，同时提供 Web 界面供用户主动占卜和查看历史运势。

### 1.2 核心特性

- **生辰八字排盘**：根据出生年月日时，精确排算四柱、五行、十神、大运
- **每日运势播报**：综合八字 + 流日推算事业/财运/感情/健康等维度运势
- **周易六爻占卜**：用户输入问题，起卦并给出卦象解读
- **奇门遁甲时盘**：排盘分析九星、八门、八神落宫
- **双通道推送**：QQ 邮箱 + 飞书机器人
- **用户反馈闭环**：评分 + 标签 + 文字反馈，影响后续解读风格
- **Web 界面**：Vue 3 前端，完整用户体系

### 1.3 目标用户

任何对命理运势感兴趣的用户，注册后即可获得个性化服务。

---

## 二、系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────┐
│                    用户浏览器                         │
│              Vue 3 + Element Plus 前端               │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP API (RESTful)
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI 后端                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ 用户模块  │ │ 运势模块  │ │ 占卜模块  │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘            │
│       │            │            │                   │
│  ┌────▼────────────▼────────────▼─────┐            │
│  │         命理计算引擎                 │            │
│  │  (lunar-python + 自研规则库)         │            │
│  └────────────┬───────────────────────┘            │
│               │ 计算结果                             │
│  ┌────────────▼───────────────────────┐            │
│  │         DeepSeek API 解读           │            │
│  └────────────┬───────────────────────┘            │
│               │                                     │
│  ┌────────────▼───────────────────────┐            │
│  │         推送服务                    │            │
│  │     QQ 邮箱 + 飞书机器人            │            │
│  └────────────────────────────────────┘            │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   MySQL 数据库   │
              └─────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | Vue 3 + Element Plus + Vite | 响应式 SPA |
| 后端 | Python + FastAPI | 高性能异步 API |
| 数据库 | MySQL | 关系型存储 |
| ORM | SQLAlchemy 2.x | 数据库映射 |
| 命理计算 | lunar-python + 自研模块 | 八字排盘、万年历 |
| LLM | DeepSeek API | 命理解读 |
| 推送 | SMTP + 飞书 Webhook | 双通道推送 |
| 定时任务 | GitHub Actions | 每日定时触发 |
| 认证 | JWT | 用户鉴权 |

---

## 三、数据库设计

### 3.1 users 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| username | VARCHAR(50) | 用户名 |
| email | VARCHAR(255) | 邮箱（登录用） |
| phone | VARCHAR(20) | 手机号 |
| password_hash | VARCHAR(255) | 密码哈希 |
| birth_year | INT | 出生年 |
| birth_month | INT | 出生月 |
| birth_day | INT | 出生日 |
| birth_hour | INT | 出生时（0-23） |
| gender | TINYINT | 性别 0=女 1=男 |
| birth_location | VARCHAR(100) | 出生地（真太阳时校正） |
| push_channel | VARCHAR(20) | 推送渠道：email/feishu/both |
| push_enabled | BOOLEAN | 是否开启每日推送 |
| feishu_webhook | VARCHAR(500) | 飞书机器人 Webhook URL |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 3.2 bazi_profiles 八字档案表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| user_id | BIGINT FK | 关联用户 |
| year_pillar | VARCHAR(4) | 年柱（如"甲子"） |
| month_pillar | VARCHAR(4) | 月柱 |
| day_pillar | VARCHAR(4) | 日柱 |
| hour_pillar | VARCHAR(4) | 时柱 |
| day_master | VARCHAR(2) | 日主天干 |
| five_elements | JSON | 五行分布 {金:3, 木:2, ...} |
| ten_gods | JSON | 十神关系 |
| major_luck_cycles | JSON | 大运排列 |
| favorable_elements | JSON | 喜用神 |
| created_at | TIMESTAMP | 创建时间 |

### 3.3 daily_fortunes 每日运势表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| user_id | BIGINT FK | 关联用户 |
| date | DATE | 运势日期 |
| heavenly_stem | VARCHAR(2) | 当日天干 |
| earthly_branch | VARCHAR(2) | 当日地支 |
| overall_score | TINYINT | 综合评分 1-5 |
| career_fortune | JSON | 事业运势详情 |
| wealth_fortune | JSON | 财运详情 |
| love_fortune | JSON | 感情运势详情 |
| health_fortune | JSON | 健康运势详情 |
| lucky_color | VARCHAR(20) | 幸运色 |
| lucky_number | VARCHAR(20) | 幸运数字 |
| lucky_direction | VARCHAR(20) | 吉利方位 |
| llm_interpretation | TEXT | LLM 解读全文 |
| user_rating | TINYINT | 用户评分 1-5 |
| user_feedback_tags | JSON | 反馈标签 ["准","有帮助"] |
| user_feedback_text | TEXT | 用户文字反馈 |
| created_at | TIMESTAMP | 创建时间 |

### 3.4 divination_records 占卜记录表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| user_id | BIGINT FK | 关联用户 |
| type | VARCHAR(20) | 类型：liuyao/qimen |
| question | TEXT | 用户问题 |
| raw_data | JSON | 原始卦象/盘面数据 |
| llm_interpretation | TEXT | LLM 解读全文 |
| user_rating | TINYINT | 用户评分 |
| user_feedback_text | TEXT | 用户文字反馈 |
| created_at | TIMESTAMP | 创建时间 |

### 3.5 索引设计

```sql
-- 用户表
UNIQUE INDEX idx_users_email ON users(email);
UNIQUE INDEX idx_users_username ON users(username);

-- 八字档案
INDEX idx_bazi_user ON bazi_profiles(user_id);

-- 每日运势
INDEX idx_fortune_user_date ON daily_fortunes(user_id, date);
UNIQUE INDEX idx_fortune_unique ON daily_fortunes(user_id, date);

-- 占卜记录
INDEX idx_divination_user ON divination_records(user_id);
```

---

## 四、核心模块设计

### 4.1 命理计算引擎

```
fortune_engine/
├── __init__.py
├── bazi/                    # 八字排盘
│   ├── __init__.py
│   ├── calendar.py          # 万年历、阴阳历转换
│   ├── pillar.py            # 天干地支排盘（年月日时四柱）
│   ├── five_element.py      # 五行分析（旺衰、喜忌）
│   ├── ten_god.py           # 十神关系计算
│   ├── luck_cycle.py        # 大运、流年排盘
│   └── daily_fortune.py     # 每日运势推算（综合流日干支）
├── liuyao/                  # 六爻占卜
│   ├── __init__.py
│   ├── hexagram.py          # 起卦（铜钱法、时间起卦）
│   └── interpret.py         # 卦象基础解读规则
├── qimen/                   # 奇门遁甲
│   ├── __init__.py
│   ├── chart.py             # 排盘（时家奇门）
│   └── analysis.py          # 九星、八门、八神落宫分析
└── common/                  # 公共工具
    ├── __init__.py
    ├── tiangan.py           # 天干定义（甲乙丙丁...）
    ├── dizhi.py             # 地支定义（子丑寅卯...）
    ├── wuxing.py            # 五行生克关系
    └── shichen.py           # 时辰对照
```

### 4.2 DeepSeek 解读服务

```python
# services/llm_service.py

PROMPT_TEMPLATE = """
你是一位精通周易、八字命理、奇门遁甲的资深命理师，有30年实战经验。

## 用户信息
- 性别：{gender}
- 生辰：{birth_info}
- 八字：{bazi}
- 五行：{five_elements}
- 喜用神：{favorable_elements}

## 今日信息
- 流日干支：{daily_stem_branch}
- 各维度原始推算数据：{raw_fortune_data}

## 用户历史反馈偏好
{user_feedback_summary}

## 任务要求
1. 基于以上数据，用专业但易懂的语言解读今日运势
2. 分事业、财运、感情、健康四个维度
3. 给出实用建议（今日宜忌、注意事项）
4. 根据用户反馈偏好调整风格和重点
5. 结尾给出幸运色、幸运数字、吉利方位
"""
```

### 4.3 推送服务

**QQ 邮箱推送（SMTP）：**
- 使用 QQ 邮箱 SMTP 服务器发送
- HTML 格式运势报告，带样式美化
- 支持每日运势推送 + 占卜结果推送

**飞书机器人推送：**
- 使用飞书自定义机器人 Webhook
- 消息卡片格式，支持富文本
- 用户在飞书中配置自己的 Webhook URL

### 4.4 用户反馈机制

```
反馈收集：
  用户在 Web 界面对每条运势/占卜结果进行反馈
  ├── 评分：1-5 星
  ├── 标签：准/不准/有帮助/需改进
  └── 文字反馈：自由文本

反馈存储：
  存入 daily_fortunes / divination_records 表的反馈字段

反馈应用：
  1. 汇总用户历史反馈（最近 30 条）
  2. 生成反馈摘要（如"用户更关注事业运，觉得财运分析很准"）
  3. 作为 prompt 的一部分传给 DeepSeek
  4. LLM 解读时参考用户偏好，调整风格和重点
```

---

## 五、每日运势推送流程

```
GitHub Actions 定时触发（每天早上 7:00 CST）
    │
    ▼
调用 POST /api/v1/internal/daily-push
    │
    ▼
查询所有 push_enabled = TRUE 的用户
    │
    ▼
对每个用户（并发处理）：
    │
    ├─ 1. 读取八字档案 (bazi_profiles)
    ├─ 2. 计算今日流日干支
    ├─ 3. 推算今日各维度运势数据
    ├─ 4. 读取用户最近 30 条反馈摘要
    ├─ 5. 组装 prompt → 调用 DeepSeek API
    ├─ 6. 生成运势报告（HTML 格式）
    ├─ 7. 根据 push_channel 推送：
    │      ├── email → QQ 邮箱 SMTP
    │      ├── feishu → 飞书 Webhook
    │      └── both → 两者都发
    └─ 8. 存入 daily_fortunes 表
```

---

## 六、Web 前端功能规划

### 6.1 页面结构

| 页面 | 功能 | 路由 |
|------|------|------|
| 首页 | 产品介绍、注册入口 | / |
| 注册 | 填写账号 + 生辰信息 | /register |
| 登录 | 邮箱/用户名登录 | /login |
| 每日运势 | 今日运势卡片、历史运势列表 | /fortune |
| 占卜中心 | 六爻占卜、奇门遁甲 | /divination |
| 个人中心 | 编辑生辰、推送设置、反馈历史 | /profile |
| 运势详情 | 单条运势完整内容 + 反馈入口 | /fortune/:id |

### 6.2 核心交互

- **注册时**：填写生辰信息 → 实时排盘预览 → 确认后保存
- **查看运势**：卡片式展示，左右滑动切换日期
- **占卜流程**：输入问题 → 选择占卜方式 → 起卦动画 → 展示解读
- **反馈操作**：每条运势底部有"准确度评分"和"反馈"按钮

---

## 七、API 接口设计

### 7.1 认证模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/register | 注册（含生辰信息） |
| POST | /api/v1/auth/login | 登录，返回 JWT |
| POST | /api/v1/auth/refresh | 刷新 Token |

### 7.2 用户模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/users/me | 获取个人信息 |
| PUT | /api/v1/users/me | 更新个人信息 |
| PUT | /api/v1/users/me/birth | 更新生辰信息 |
| PUT | /api/v1/users/me/push-settings | 更新推送设置 |

### 7.3 运势模块

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/fortunes/today | 获取今日运势 |
| GET | /api/v1/fortunes | 历史运势列表（分页） |
| GET | /api/v1/fortunes/:id | 运势详情 |
| POST | /api/v1/fortunes/:id/feedback | 提交反馈 |

### 7.4 占卜模块

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/divination/liuyao | 六爻占卜 |
| POST | /api/v1/divination/qimen | 奇门遁甲 |
| GET | /api/v1/divination/records | 占卜历史 |
| POST | /api/v1/divination/:id/feedback | 占卜反馈 |

### 7.5 内部接口（GitHub Actions 调用）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/internal/daily-push | 触发每日运势推送 |

---

## 八、GitHub Actions 定时任务

```yaml
# .github/workflows/daily-fortune.yml
name: Daily Fortune Push
on:
  schedule:
    - cron: '0 23 * * *'  # UTC 23:00 = 北京时间 07:00
  workflow_dispatch:  # 手动触发

jobs:
  push-fortune:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/daily_push.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
```

---

## 九、环境变量配置

```env
# .env（本地开发用，不提交 Git）
# .env.example（模板，提交 Git）

# 数据库
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/fortune

# DeepSeek API
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# QQ 邮箱 SMTP
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your-qq@qq.com
SMTP_PASSWORD=your-smtp-password

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRE_HOURS=24

# 应用配置
APP_PORT=8000
APP_ENV=development
```

---

## 十、目录结构总览

```
E:/fortune/
├── docs/
│   └── plans/
│       └── 2026-06-20-fortune-agent-design.md  # 本文档
├── server/                          # 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── config.py                # 配置管理
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py          # 认证接口
│   │   │   │   ├── users.py         # 用户接口
│   │   │   │   ├── fortunes.py      # 运势接口
│   │   │   │   ├── divination.py    # 占卜接口
│   │   │   │   └── internal.py      # 内部接口（定时任务）
│   │   │   └── deps.py              # 依赖注入
│   │   ├── models/                  # SQLAlchemy 模型
│   │   ├── schemas/                 # Pydantic Schema
│   │   ├── services/                # 业务逻辑
│   │   ├── repositories/            # 数据访问
│   │   └── core/
│   │       ├── security.py          # JWT/密码
│   │       └── exceptions.py        # 自定义异常
│   ├── fortune_engine/              # 命理计算引擎
│   │   ├── bazi/                    # 八字排盘
│   │   ├── liuyao/                  # 六爻占卜
│   │   ├── qimen/                   # 奇门遁甲
│   │   └── common/                  # 公共工具
│   ├── services/
│   │   ├── llm_service.py           # DeepSeek API 调用
│   │   ├── email_service.py         # QQ 邮箱推送
│   │   └── feishu_service.py        # 飞书推送
│   ├── scripts/
│   │   └── daily_push.py            # 每日推送脚本
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic/                     # 数据库迁移
├── client/                          # 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/
│   │   ├── stores/
│   │   ├── views/
│   │   │   ├── Home.vue
│   │   │   ├── Login.vue
│   │   │   ├── Register.vue
│   │   │   ├── Fortune.vue
│   │   │   ├── Divination.vue
│   │   │   └── Profile.vue
│   │   ├── components/
│   │   └── api/
│   ├── package.json
│   └── vite.config.ts
├── .github/
│   └── workflows/
│       └── daily-fortune.yml
├── .gitignore
├── .env.example
├── TECH_STACK.md
└── README.md
```

---

## 十一、开发阶段规划

### Phase 1：基础骨架（预计 2-3 天）
- 项目初始化（后端 + 前端）
- 数据库建表 + ORM 模型
- 用户注册/登录（JWT 认证）
- 前端基础页面框架

### Phase 2：命理计算引擎（预计 3-4 天）
- 八字排盘核心算法
- 五行/十神/大运计算
- 每日运势推算
- DeepSeek 解读服务对接

### Phase 3：运势推送系统（预计 2 天）
- QQ 邮箱 SMTP 推送
- 飞书机器人 Webhook 推送
- 每日定时推送流程
- GitHub Actions 配置

### Phase 4：Web 功能完善（预计 2-3 天）
- 每日运势页面
- 用户反馈功能
- 个人中心 + 推送设置

### Phase 5：占卜功能（预计 2-3 天）
- 六爻占卜模块
- 奇门遁甲模块
- 占卜历史 + 反馈

### Phase 6：优化上线（预计 1-2 天）
- UI 美化
- 错误处理完善
- 部署配置
- 文档编写

---

## 十二、关键技术难点

| 难点 | 说明 | 解决方案 |
|------|------|---------|
| 八字排盘准确性 | 需要考虑真太阳时、闰月等 | 使用 lunar-python 成熟库 + 自研校验 |
| 奇门遁甲排盘 | 时家奇门排盘逻辑复杂 | 参考经典算法实现，编写单元测试验证 |
| DeepSeek 输出稳定性 | LLM 输出可能格式不一致 | 结构化 prompt + 输出后处理 |
| 并发推送性能 | 多用户同时推送 | 异步并发 + 速率限制 |
| 用户反馈应用 | 如何有效利用反馈数据 | 摘要化反馈 + prompt 注入 |

---

*文档结束*
