# Spec 014: DeepSeek 解读服务

> 模块：LLM 解读服务 | 优先级：P0 | 预计：1 天

## 功能描述

封装 DeepSeek API 调用，将命理计算结果转化为专业易懂的解读文字。

## 核心 Prompt 模板

```
你是一位精通周易、八字命理、奇门遁甲的资深命理师。

## 用户信息
- 性别：{gender}
- 生辰：{birth_info}
- 八字：{bazi}
- 五行：{five_elements}
- 喜用神：{favorable_elements}

## 推算数据
{calculation_result}

## 用户历史反馈偏好
{user_feedback_summary}

## 任务要求
1. 用专业但易懂的语言解读
2. 给出实用建议
3. 根据用户反馈偏好调整风格和重点
```

## 验收标准

```
Scenario: 八字解读正常
  Given 用户八字数据和五行分析
  When  调用 DeepSeek 解读
  Then  应返回专业且易懂的命理解读
  And   应分事业、财运、感情、健康四个维度
  And   应包含实用建议

Scenario: API 故障时降级
  Given DeepSeek API 返回错误
  When  调用解读服务
  Then  应返回降级结果 "今日解读暂不可用"
  And   不应报错崩溃

Scenario: 输出格式稳定
  Given 相同输入数据
  When  多次调用解读服务
  Then  输出格式应保持一致
```

## 技术要点

- 使用 httpx 异步调用 DeepSeek API
- 超时设置：30 秒
- 重试策略：最多 3 次
- 降级策略：API 故障时返回纯算法结果
- 输出后处理：提取关键信息、格式化

## 依赖项

- 前置：010-八字排盘、011-每日运势推算
- 外部：DeepSeek API
