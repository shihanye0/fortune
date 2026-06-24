<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import {
  doLiuyao,
  doQimen,
  getDivinationRecords,
  getDivinationDetail,
  submitDivinationFeedback,
  getProbabilityEvents,
  submitEventFeedback,
} from '../api/divination-api'
import type { DivinationResult, DivinationRecord, ProbabilityEvent, EventFeedbackRequest } from '../api/divination-api'
import { submitDivinationAccuracy, submitPredictionOutcome } from '@/features/feedback/api/feedback-api'

const loading = ref(false)
const method = ref<'liuyao' | 'qimen'>('liuyao')
const qimenMode = ref<'question' | 'realtime'>('realtime')
const question = ref('')
const result = ref<DivinationResult | null>(null)
const historyList = ref<DivinationRecord[]>([])
const showFeedback = ref(false)
const feedbackRating = ref(5)
const feedbackText = ref('')

// 概率事件数据（从 API 获取）
const probabilityEvents = ref<ProbabilityEvent[]>([])
const loadingEvents = ref(false)

// 事件反馈弹窗
const showEventFeedbackDialog = ref(false)
const feedbackEvent = ref<ProbabilityEvent | null>(null)
const eventFeedbackForm = reactive<EventFeedbackRequest>({
  dimension: '',
  event_name: '',
  probability: 0,
  occurred: undefined,
  rating: undefined,
  feedback_text: '',
})
const submittingEventFeedback = ref(false)

// 查看详情
const showDetailDialog = ref(false)
const selectedRecord = ref<DivinationRecord | null>(null)
const detailInterpretation = ref('')
const loadingDetail = ref(false)

async function viewDetail(record: DivinationRecord) {
  selectedRecord.value = record
  showDetailDialog.value = true
  loadingDetail.value = true
  detailInterpretation.value = ''

  try {
    const res = await getDivinationDetail(record.id)
    if (res.success) {
      detailInterpretation.value = res.data.interpretation || '暂无解读'
    }
  } catch {
    detailInterpretation.value = '加载失败'
  } finally {
    loadingDetail.value = false
  }
}

// 获取概率事件
async function fetchProbabilityEvents() {
  loadingEvents.value = true
  try {
    const res = await getProbabilityEvents()
    if (res.success && res.data) {
      probabilityEvents.value = res.data.events
    }
  } catch {
    // silent
  } finally {
    loadingEvents.value = false
  }
}

// 打开事件反馈弹窗
function openEventFeedback(event: ProbabilityEvent) {
  feedbackEvent.value = event
  eventFeedbackForm.dimension = event.dimension
  eventFeedbackForm.event_name = event.event
  eventFeedbackForm.probability = event.probability
  eventFeedbackForm.occurred = event.feedback?.occurred ?? undefined
  eventFeedbackForm.rating = event.feedback?.rating ?? undefined
  eventFeedbackForm.feedback_text = event.feedback?.feedback_text ?? ''
  showEventFeedbackDialog.value = true
}

// 提交事件反馈
async function handleSubmitEventFeedback() {
  if (!feedbackEvent.value) return
  submittingEventFeedback.value = true
  try {
    const res = await submitEventFeedback(eventFeedbackForm)
    if (res.success) {
      ElMessage.success('反馈提交成功')
      showEventFeedbackDialog.value = false
      // 更新本地数据
      if (feedbackEvent.value) {
        feedbackEvent.value.feedback = {
          occurred: eventFeedbackForm.occurred ?? null,
          rating: eventFeedbackForm.rating ?? null,
          feedback_text: eventFeedbackForm.feedback_text ?? null,
        }
      }
    }
  } catch {
    ElMessage.error('提交失败，请重试')
  } finally {
    submittingEventFeedback.value = false
  }
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
  fetchProbabilityEvents()
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

// 准确性标记
const markingAccuracy = ref(false)

async function handleAccuracyMark(recordId: number, mark: number) {
  markingAccuracy.value = true
  try {
    const res = await submitDivinationAccuracy(recordId, mark)
    if (res.success) {
      // 更新详情弹窗中的数据
      if (selectedRecord.value && selectedRecord.value.id === recordId) {
        selectedRecord.value.accuracy_mark = mark
      }
      // 更新历史列表中的数据
      const idx = historyList.value.findIndex(r => r.id === recordId)
      if (idx >= 0) {
        historyList.value[idx].accuracy_mark = mark
      }
      ElMessage.success(mark === 1 ? '已标记为准确' : '已标记为不准确')
    }
  } catch {
    ElMessage.error('标记失败，请重试')
  } finally {
    markingAccuracy.value = false
  }
}

// 事件验证
const showVerifyDialog = ref(false)
const verifyForm = reactive({
  outcome_text: '',
  verified: true as boolean,
})
const submittingVerify = ref(false)

function openVerifyDialog() {
  verifyForm.outcome_text = ''
  verifyForm.verified = true
  showVerifyDialog.value = true
}

async function handleSubmitVerify() {
  if (!selectedRecord.value) return
  if (!verifyForm.outcome_text.trim()) {
    ElMessage.warning('请填写结果描述')
    return
  }
  submittingVerify.value = true
  try {
    const res = await submitPredictionOutcome({
      source_type: 'divination',
      source_id: selectedRecord.value.id,
      outcome_text: verifyForm.outcome_text,
      verified: verifyForm.verified,
    })
    if (res.success) {
      // 更新列表状态
      if (selectedRecord.value) {
        selectedRecord.value.outcome_verified = true
      }
      const idx = historyList.value.findIndex(r => r.id === selectedRecord.value?.id)
      if (idx >= 0) {
        historyList.value[idx].outcome_verified = true
      }
      showVerifyDialog.value = false
      ElMessage.success('事件验证提交成功')
    }
  } catch {
    ElMessage.error('提交失败，请重试')
  } finally {
    submittingVerify.value = false
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
    <el-card class="daily-events-card animate-fade-in" v-loading="loadingEvents">
      <template #header>
        <div class="card-header">
          <span class="card-icon">📊</span>
          <span class="card-title">今日概率事件</span>
          <el-tag type="info" effect="plain" size="small">{{ new Date().toLocaleDateString('zh-CN') }}</el-tag>
          <el-tag v-if="probabilityEvents.length > 0" type="success" effect="plain" size="small">
            基于您的八字推算
          </el-tag>
        </div>
      </template>
      <div class="events-grid" v-if="probabilityEvents.length > 0">
        <div v-for="(item, index) in probabilityEvents" :key="index" class="event-item">
          <div class="event-icon">{{ item.icon }}</div>
          <div class="event-content">
            <div class="event-header">
              <span class="event-name">{{ item.event }}</span>
              <el-tag size="small" :type="item.is_favorable ? 'success' : 'info'">
                {{ item.time_range }}
              </el-tag>
            </div>
            <div class="event-desc">{{ item.description }}</div>
            <div class="event-meta">
              <el-tag v-if="item.ten_god" size="small" type="warning">{{ item.ten_god }}</el-tag>
              <el-tag v-if="item.element" size="small">{{ item.element }}</el-tag>
              <el-tag v-if="item.is_favorable" size="small" type="success">喜用神</el-tag>
            </div>
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
            <div class="event-feedback">
              <el-button
                v-if="!item.feedback"
                size="small"
                type="primary"
                plain
                @click.stop="openEventFeedback(item)"
              >
                反馈
              </el-button>
              <el-tag
                v-else-if="item.feedback.occurred === true"
                type="success"
                size="small"
                effect="plain"
              >
                ✓ 已发生
              </el-tag>
              <el-tag
                v-else-if="item.feedback.occurred === false"
                type="info"
                size="small"
                effect="plain"
              >
                ✗ 未发生
              </el-tag>
              <el-button
                v-if="item.feedback"
                size="small"
                type="primary"
                plain
                @click.stop="openEventFeedback(item)"
              >
                修改
              </el-button>
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="!loadingEvents" class="empty-events">
        暂无概率事件数据
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
          <div v-if="loadingDetail" class="loading-text">加载中...</div>
          <div v-else class="interpretation-text">
            {{ detailInterpretation }}
          </div>
        </div>
        <div class="detail-rating" v-if="selectedRecord.user_rating">
          <span class="meta-label">您的评价：</span>
          <span class="rating-stars">{{ '★'.repeat(selectedRecord.user_rating) }}{{ '☆'.repeat(5 - selectedRecord.user_rating) }}</span>
        </div>
        <el-divider />
        <div class="accuracy-section">
          <div class="accuracy-label">这个解读准确吗？</div>
          <div v-if="selectedRecord.accuracy_mark !== null && selectedRecord.accuracy_mark !== undefined" class="accuracy-marked">
            <el-tag :type="selectedRecord.accuracy_mark === 1 ? 'success' : 'danger'" effect="dark" size="large">
              {{ selectedRecord.accuracy_mark === 1 ? '✓ 已标记为准确' : '✗ 已标记为不准确' }}
            </el-tag>
          </div>
          <div v-else class="accuracy-buttons">
            <el-button
              type="success"
              :loading="markingAccuracy"
              @click="handleAccuracyMark(selectedRecord.id, 1)"
            >
              👍 准确
            </el-button>
            <el-button
              type="danger"
              :loading="markingAccuracy"
              @click="handleAccuracyMark(selectedRecord.id, 0)"
            >
              👎 不准确
            </el-button>
          </div>
        </div>
        <div class="verify-section">
          <el-button
            v-if="!selectedRecord.outcome_verified"
            type="warning"
            @click="openVerifyDialog"
          >
            🔍 验证事件结果
          </el-button>
          <el-tag v-else type="info" effect="plain" size="large">
            ✓ 事件结果已验证
          </el-tag>
        </div>
      </div>
    </el-dialog>

    <!-- 概率事件反馈弹窗 -->
    <el-dialog
      v-model="showEventFeedbackDialog"
      title="概率事件反馈"
      width="480px"
      class="event-feedback-dialog"
    >
      <div v-if="feedbackEvent" class="event-feedback-content">
        <div class="feedback-event-info">
          <div class="feedback-event-icon">{{ feedbackEvent.icon }}</div>
          <div class="feedback-event-name">{{ feedbackEvent.event }}</div>
          <div class="feedback-event-desc">{{ feedbackEvent.description }}</div>
          <div class="feedback-event-prob">预测概率：{{ feedbackEvent.probability }}%</div>
        </div>
        <el-divider />
        <el-form label-position="top">
          <el-form-item label="事件是否发生">
            <el-radio-group v-model="eventFeedbackForm.occurred">
              <el-radio :value="true">确实发生</el-radio>
              <el-radio :value="false">未发生</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="预测准确度评分">
            <el-rate v-model="eventFeedbackForm.rating" :max="5" />
          </el-form-item>
          <el-form-item label="补充说明（选填）">
            <el-input
              v-model="eventFeedbackForm.feedback_text"
              type="textarea"
              :rows="3"
              placeholder="可以描述具体发生了什么..."
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showEventFeedbackDialog = false">取消</el-button>
        <el-button type="primary" :loading="submittingEventFeedback" @click="handleSubmitEventFeedback">
          提交反馈
        </el-button>
      </template>
    </el-dialog>

    <!-- 事件验证弹窗 -->
    <el-dialog
      v-model="showVerifyDialog"
      title="验证事件结果"
      width="480px"
      class="verify-dialog"
    >
      <el-form label-position="top">
        <el-form-item label="结果描述">
          <el-input
            v-model="verifyForm.outcome_text"
            type="textarea"
            :rows="4"
            placeholder="请描述这个预测的实际结果..."
          />
        </el-form-item>
        <el-form-item label="事件是否发生">
          <el-radio-group v-model="verifyForm.verified">
            <el-radio :value="true">确实发生</el-radio>
            <el-radio :value="false">未发生</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showVerifyDialog = false">取消</el-button>
        <el-button type="primary" :loading="submittingVerify" @click="handleSubmitVerify">
          提交验证
        </el-button>
      </template>
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

.event-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.event-feedback {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.empty-events {
  text-align: center;
  padding: 40px;
  color: var(--color-text-secondary);
}

/* 事件反馈弹窗 */
.event-feedback-content {
  padding: 8px 0;
}

.feedback-event-info {
  text-align: center;
  padding: 16px;
  background: var(--color-bg-light);
  border-radius: 12px;
}

.feedback-event-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.feedback-event-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}

.feedback-event-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.feedback-event-prob {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-accent);
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

/* 准确性标记 */
.accuracy-section {
  text-align: center;
  padding: 16px 0;
}

.accuracy-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
}

.accuracy-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.accuracy-marked {
  display: flex;
  justify-content: center;
}

/* 事件验证 */
.verify-section {
  text-align: center;
  padding: 8px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .events-grid {
    grid-template-columns: 1fr;
  }
}
</style>
