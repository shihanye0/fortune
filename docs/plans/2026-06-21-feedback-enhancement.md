# 反馈系统增强计划

## 目标
实现 4 种反馈方式，让反馈能影响后续推演：
1. 准确性反馈（准/不准）
2. 事件关联反馈（预测事件是否发生）
3. 维度偏好反馈（关注哪些维度）
4. 准确率追踪（统计历史准确率，影响推演权重）

## 任务清单

### Task 1: 数据库模型增强
- 新增 `prediction_outcomes` 表（事件验证记录）
- `daily_fortunes` 表新增 `accuracy_mark` 字段（准/不准标记）
- `divination_records` 表新增 `accuracy_mark` 和 `outcome_verified` 字段

### Task 2: 后端 API - 事件验证与准确率
- POST `/api/v1/fortunes/{id}/accuracy` — 标记运势准确性
- POST `/api/v1/divination/{id}/accuracy` — 标记占卜准确性
- POST `/api/v1/prediction-outcomes` — 提交事件验证
- GET `/api/v1/users/me/accuracy-stats` — 获取准确率统计

### Task 3: 后端服务 - 增强反馈摘要
- feedback_summary 中加入准确率数据
- 新增维度偏好权重计算
- LLM prompt 中加入历史准确率

### Task 4: 前端 API 层
- 新增 accuracyApi.ts
- 新增 outcomeApi.ts
- 更新类型定义

### Task 5: 前端 UI - 反馈组件与仪表盘
- 运势详情中添加准确性标记按钮
- 占卜详情中添加准确性标记按钮
- 事件验证弹窗
- 个人中心添加准确率仪表盘
