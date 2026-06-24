# Spec 014: LLM 解读服务

> 模块：LLM 解读服务 | 优先级：P0

## 功能描述

封装 LLM API 调用，将命理计算结果转化为专业易懂的解读文字。

## 当前供应商

| 项目 | 值 |
|------|------|
| 供应商 | Xiaomi MiMo |
| API URL | `https://token-plan-cn.xiaomimimo.com/v1` |
| 模型 | `mimo-v2.5` |
| 格式 | OpenAI 兼容（`/chat/completions`） |

## 配置层级

LLM 配置采用**用户级覆盖 + 服务器默认**机制：

1. **用户配置**（个人中心 → LLM 配置）→ 优先使用
2. **服务器默认**（`.env` 文件）→ 用户未配置时回退

用户可在个人中心配置：供应商名称、备注、官网链接、API Key、请求地址、模型名称，并支持「测试连接」验证配置是否正确。

## 核心 Prompt 模板

```
你是一位精通命理的运势播报师。请根据以下数据生成今日运势播报。

八字概要：{bazi_summary}
今日运势数据：{fortune_data}
用户偏好：{user_feedback_summary}
历史准确率：{accuracy_info}

重要格式要求（必须严格遵守）：
- 禁止使用任何 markdown 格式符号
- 直接用纯文字描述，像平时聊天一样
- 事业、财运、感情、健康各用 2-3 句话自然描述
- 最后给 2-3 条实用建议
- 总字数控制在 200-300 字
```

## 验收标准

```
Scenario: 八字解读正常
  Given 用户八字数据和五行分析
  When  调用 LLM 解读
  Then  应返回专业且易懂的命理解读
  And   应分事业、财运、感情、健康四个维度
  And   应包含实用建议

Scenario: API 故障时降级
  Given LLM API 返回错误
  When  调用解读服务
  Then  应返回降级结果 "今日详细解读暂不可用"
  And   不应报错崩溃

Scenario: 用户级配置覆盖
  Given 用户在个人中心配置了自定义 LLM
  When  生成运势解读
  Then  应使用用户配置而非服务器默认

Scenario: 模型名称自动清理
  Given 模型名称包含上下文标注（如 mimo-v2.5[1M]）
  When  调用 API
  Then  应自动去掉 [1M] 等标注
```

## 技术要点

- 使用 httpx 同步调用 LLM API
- 超时设置：30 秒（前端 regenerate 接口超时 60 秒）
- 重试策略：最多 2 次
- 降级策略：API 故障时返回降级文本
- 输出后处理：清除 markdown 格式标记
- 模型名称清理：去掉 `[1M]` 等上下文窗口标注

## 依赖项

- 前置：010-八字排盘、011-每日运势推算
- 外部：Xiaomi MiMo API（OpenAI 兼容格式）
