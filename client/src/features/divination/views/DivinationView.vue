<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  doLiuyao,
  doQimen,
  getDivinationRecords,
  submitDivinationFeedback,
} from '../api/divination-api'
import type { DivinationResult, DivinationRecord } from '../api/divination-api'

const loading = ref(false)
const method = ref<'liuyao' | 'qimen'>('liuyao')
const qimenMode = ref<'question' | 'realtime'>('realtime')
const question = ref('')
const result = ref<DivinationResult | null>(null)
const historyList = ref<DivinationRecord[]>([])
const showFeedback = ref(false)
const feedbackRating = ref(5)
const feedbackText = ref('')

// 查看详情
const showDetailDialog = ref(false)
const selectedRecord = ref<DivinationRecord | null>(null)

function viewDetail(record: DivinationRecord) {
  selectedRecord.value = record
  showDetailDialog.value = true
}

// 每日概率事件（更精细）
const dailyEvents = ref([
  {
    icon: '💼',
    event: '工作机遇',
    probability: 0,
    description: '可能收到面试邀请、项目合作或升职加薪的机会',
    timeRange: '上午 9-11 点',
    advice: '保持专注，主动沟通',
  },
  {
    icon: '💰',
    event: '偏财运',
    probability: 0,
    description: '可能有意外收入、中奖或投资回报',
    timeRange: '下午 2-4 点',
    advice: '理性消费，避免冲动',
  },
  {
    icon: '💕',
    event: '桃花运',
    probability: 0,
    description: '可能遇到心仪对象或收到表白',
    timeRange: '晚上 7-9 点',
    advice: '主动出击，把握机会',
  },
  {
    icon: '🤝',
    event: '贵人相助',
    probability: 0,
    description: '可能得到长辈、朋友或同事的帮助',
    timeRange: '全天',
    advice: '虚心请教，感恩回报',
  },
])

// 生成随机概率（基于今日日期）
function generateProbabilities() {
  const today = new Date()
  const seed = today.getFullYear() * 10000 + (today.getMonth() + 1) * 100 + today.getDate()

  dailyEvents.value.forEach((event, index) => {
    // 使用简单的伪随机算法，确保同一天概率相同
    const random = Math.sin(seed * (index + 1) * 9301 + 49297) % 233280
    event.probability = Math.floor((Math.abs(random) / 233280) * 40 + 30) // 30-70%
  })
}

function getProbabilityColor(prob: number): string {
  if (prob >= 60) return '#22c55e'
  if (prob >= 40) return '#eab308'
  return '#ef4444'
}

function getProbabilityText(prob: number): string {
  if (prob >= 60) return '较高'
  if (prob >= 40) return '中等'
  return '较低'
}

onMounted(async () => {
  generateProbabilities()
  try {
    const res = await getDivinationRecords()
    if (res.success) {
      historyList.value = res.data
    }
  } catch {
    // silent
  }
})

async function handleSubmit() {
  loading.value = true
  result.value = null
  try {
    let res
    if (method.value === 'liuyao') {
      res = await doLiuyao({ question: question.value || undefined, method: 'coin' })
    } else {
      res = await doQimen({ question: question.value || undefined, mode: qimenMode.value })
    }
    if (res.success) {
      result.value = res.data
      // Refresh history
      const histRes = await getDivinationRecords()
      if (histRes.success) historyList.value = histRes.data
    } else {
      ElMessage.error(res.error?.message || '占卜失败')
    }
  } catch {
    ElMessage.error('网络错误，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function handleSubmitFeedback() {
  if (!result.value) return
  try {
    const res = await submitDivinationFeedback(result.value.id, {
      rating: feedbackRating.value,
      feedback_text: feedbackText.value || undefined,
    })
    if (res.success) {
      showFeedback.value = false
      ElMessage.success('反馈提交成功')
    }
  } catch {
    ElMessage.error('提交反馈失败')
  }
}
</script>

<template>
  <div class="divination-page">
    <div class="page-header animate-fade-in">
      <h1 class="page-title">占卜中心</h1>
      <p class="page-subtitle">传统命理，智慧指引</p>
    </div>

    <!-- 每日概率事件 -->
    <el-card class="daily-events-card animate-fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-icon">📊</span>
          <span class="card-title">今日概率事件</span>
          <el-tag type="info" effect="plain" size="small">{{ new Date().toLocaleDateString('zh-CN') }}</el-tag>
        </div>
      </template>
      <div class="events-grid">
        <div v-for="(item, index) in dailyEvents" :key="index" class="event-item">
          <div class="event-icon">{{ item.icon }}</div>
          <div class="event-content">
            <div class="event-header">
              <span class="event-name">{{ item.event }}</span>
              <el-tag size="small" type="info">{{ item.timeRange }}</el-tag>
            </div>
            <div class="event-desc">{{ item.description }}</div>
            <div class="event-probability">
              <el-progress
                :percentage="item.probability"
                :color="getProbabilityColor(item.probability)"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="probability-text" :style="{ color: getProbabilityColor(item.probability) }">
                {{ item.probability }}% {{ getProbabilityText(item.probability) }}
              </span>
            </div>
            <div class="event-advice">
              <span class="advice-label">建议：</span>{{ item.advice }}
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 选择占卜方式 -->
    <el-card class="method-card animate-fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-icon">🔮</span>
          <span class="card-title">开始占卜</span>
        </div>
      </template>
      <el-radio-group v-model="method" class="method-selector">
        <el-radio-button value="liuyao">
          <span class="method-icon">☯</span>
          <span>六爻占卜</span>
        </el-radio-button>
        <el-radio-button value="qimen">
          <span class="method-icon">🌌</span>
          <span>奇门遁甲</span>
        </el-radio-button>
      </el-radio-group>

      <div v-if="method === 'qimen'" class="qimen-mode">
        <el-radio-group v-model="qimenMode">
          <el-radio value="realtime">实时看盘</el-radio>
          <el-radio value="question">一事一测</el-radio>
        </el-radio-group>
      </div>

      <div class="question-input">
        <el-input
          v-model="question"
          type="textarea"
          placeholder="输入你的问题（选填）"
          :rows="3"
        />
      </div>

      <el-button
        type="primary"
        :loading="loading"
        @click="handleSubmit"
        class="submit-btn"
      >
        {{ method === 'liuyao' ? '🎯 起卦' : '🌌 起盘' }}
      </el-button>
    </el-card>

    <!-- 结果展示 -->
    <el-card v-if="result" class="result-card animate-fade-in">
      <template #header>
        <div class="card-header">
          <span class="card-icon">{{ method === 'liuyao' ? '☯' : '🌌' }}</span>
          <span class="card-title">{{ method === 'liuyao' ? '卦象结果' : '奇门盘面' }}</span>
        </div>
      </template>

      <div v-if="result.question" class="result-question">
        <strong>问题：</strong>{{ result.question }}
      </div>

      <el-divider />

      <div class="interpretation">
        <h3 class="interpretation-title">🔮 解读</h3>
        <p class="interpretation-text">{{ result.interpretation }}</p>
      </div>

      <div class="card-actions">
        <el-button @click="showFeedback = !showFeedback" class="feedback-toggle">
          {{ showFeedback ? '收起反馈' : '📝 反馈准确度' }}
        </el-button>
      </div>

      <!-- 反馈表单 -->
      <el-card v-if="showFeedback" class="feedback-card">
        <h4>这个解读准确吗？</h4>
        <el-rate v-model="feedbackRating" :max="5" class="feedback-rate" />
        <el-input
          v-model="feedbackText"
          type="textarea"
          placeholder="补充说明（选填）"
          :rows="2"
          style="margin-top: 12px"
        />
        <el-button type="primary" @click="handleSubmitFeedback" class="submit-feedback">
          提交反馈
        </el-button>
      </el-card>
    </el-card>

    <!-- 历史记录 -->
    <div class="history-section animate-fade-in" v-if="historyList.length > 0">
      <h2 class="section-title">占卜历史</h2>
      <div class="history-list">
        <div
          v-for="record in historyList"
          :key="record.id"
          class="history-item"
          @click="viewDetail(record)"
        >
          <div class="history-header">
            <div class="history-type">
              <el-tag :type="record.type === 'liuyao' ? '' : 'success'" size="small">
                {{ record.type === 'liuyao' ? '六爻' : '奇门' }}
              </el-tag>
            </div>
            <div class="history-time">
              {{ new Date(record.created_at).toLocaleString('zh-CN') }}
            </div>
          </div>
          <div class="history-question" v-if="record.question">
            {{ record.question }}
          </div>
          <div class="history-rating" v-if="record.user_rating">
            <span class="rating-stars">{{ '★'.repeat(record.user_rating) }}{{ '☆'.repeat(5 - record.user_rating) }}</span>
          </div>
          <div class="history-arrow">→</div>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="selectedRecord?.type === 'liuyao' ? '六爻占卜详情' : '奇门遁甲详情'"
      width="600px"
      class="detail-dialog"
    >
      <div v-if="selectedRecord" class="detail-content">
        <div class="detail-meta">
          <div class="detail-time">
            <span class="meta-label">占卜时间：</span>
            {{ new Date(selectedRecord.created_at).toLocaleString('zh-CN') }}
          </div>
          <div class="detail-type">
            <span class="meta-label">占卜类型：</span>
            <el-tag :type="selectedRecord.type === 'liuyao' ? '' : 'success'" size="small">
              {{ selectedRecord.type === 'liuyao' ? '六爻' : '奇门' }}
            </el-tag>
          </div>
          <div class="detail-question" v-if="selectedRecord.question">
            <span class="meta-label">占卜问题：</span>
            {{ selectedRecord.question }}
          </div>
        </div>
        <el-divider />
        <div class="detail-interpretation">
          <h4>解读结果</h4>
          <div class="interpretation-text">
            {{ selectedRecord.summary || '暂无解读' }}
          </div>
        </div>
        <div class="detail-rating" v-if="selectedRecord.user_rating">
          <span class="meta-label">您的评价：</span>
          <span class="rating-stars">{{ '★'.repeat(selectedRecord.user_rating) }}{{ '☆'.repeat(5 - selectedRecord.user_rating) }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.divination-page {
  padding: 0;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 36px;
  font-weight: 700;
  font-family: var(--font-family-display);
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 16px;
  color: var(--color-text-secondary);
}

/* 卡片通用 */
.daily-events-card,
.method-card,
.result-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-icon {
  font-size: 24px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}

/* 每日概率事件 */
.events-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.event-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, var(--color-bg-light) 0%, var(--color-surface) 100%);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.event-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.event-icon {
  font-size: 40px;
  flex-shrink: 0;
}

.event-content {
  flex: 1;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.event-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.event-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
}

.event-probability {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.probability-text {
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
}

.event-advice {
  font-size: 12px;
  color: var(--color-accent);
  padding: 8px 12px;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 8px;
  border-left: 3px solid var(--color-accent);
}

.advice-label {
  font-weight: 600;
}

/* 占卜方式选择 */
.method-selector {
  margin-bottom: 20px;
}

.method-selector .el-radio-button {
  padding: 12px 24px;
}

.method-icon {
  display: block;
  font-size: 24px;
  margin-bottom: 4px;
}

.qimen-mode {
  margin-bottom: 20px;
}

.question-input {
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
}

/* 结果展示 */
.result-question {
  margin-bottom: 16px;
  color: var(--color-text-secondary);
}

.interpretation {
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(245, 158, 11, 0.1) 100%);
  border-radius: 12px;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.interpretation-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-accent);
}

.interpretation-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text);
}

.card-actions {
  text-align: center;
}

.feedback-toggle {
  margin-bottom: 16px;
}

.feedback-card {
  margin-top: 16px;
}

.feedback-card h4 {
  margin-bottom: 12px;
  color: var(--color-text);
}

.feedback-rate {
  margin-bottom: 12px;
}

.submit-feedback {
  margin-top: 12px;
}

/* 历史记录 */
.history-section {
  margin-top: 48px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--color-text);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--color-surface);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all 0.3s ease;
}

.history-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
  transform: translateX(4px);
}

.history-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
}

.history-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.history-question {
  flex: 1;
  font-size: 14px;
  color: var(--color-text);
}

.history-rating {
  min-width: 80px;
}

.rating-stars {
  color: #f59e0b;
  font-size: 14px;
}

.history-arrow {
  font-size: 18px;
  color: var(--color-primary);
  transition: transform 0.3s ease;
}

.history-item:hover .history-arrow {
  transform: translateX(4px);
}

/* 详情弹窗 */
.detail-dialog {
  background: var(--color-surface);
}

.detail-content {
  padding: 16px 0;
}

.detail-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-label {
  font-weight: 600;
  color: var(--color-text-secondary);
}

.detail-interpretation {
  margin-top: 16px;
}

.detail-interpretation h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text);
}

.interpretation-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text);
  padding: 16px;
  background: var(--color-bg-light);
  border-radius: 8px;
}

.detail-rating {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

/* 响应式 */
@media (max-width: 768px) {
  .events-grid {
    grid-template-columns: 1fr;
  }
}
</style>
