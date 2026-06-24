<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getTodayFortune,
  getFortuneList,
  getFortuneDetail,
  submitFortuneFeedback,
  regenerateTodayFortune,
} from '../api/fortune-api'
import type { FortuneDetail, FortuneListItem, FortuneFeedback } from '../api/fortune-api'
import { submitFortuneAccuracy } from '@/features/feedback/api/feedback-api'

const loading = ref(true)
const todayFortune = ref<FortuneDetail | null>(null)
const historyList = ref<FortuneListItem[]>([])
const showFeedback = ref(false)
const feedbackForm = ref<FortuneFeedback>({ rating: 5, tags: [], feedback_text: '' })

const feedbackTags = ['很准', '一般', '不太准', '有启发', '需要更多细节']

// 时辰运势数据（从 API 获取）
interface HourlyFortune {
  shichen: string
  shichen_range: string
  hourly_stem: string
  hourly_branch: string
  score: number
  ten_god: string
  element: string
  atmosphere: string
  energy: string
  events: string[]
  favorable: string[]
  unfavorable: string[]
}

const hourlyFortunes = ref<HourlyFortune[]>([])

// 时辰图标映射
const shichenIcons: Record<string, string> = {
  '子': '🌙', '丑': '🌑', '寅': '🌅', '卯': '🌄',
  '辰': '☀️', '巳': '🌞', '午': '⛅', '未': '🌤️',
  '申': '🌇', '酉': '🌆', '戌': '🌃', '亥': '🌌',
}

// 获取时辰图标
function getShichenIcon(shichen: string): string {
  return shichenIcons[shichen] || '⏰'
}

// 获取评分颜色
function getHourlyScoreColor(score: number): string {
  if (score >= 5) return '#22c55e'
  if (score >= 4) return '#84cc16'
  if (score >= 3) return '#eab308'
  if (score >= 2) return '#f97316'
  return '#ef4444'
}


function reloadPage() {
  window.location.reload()
}

function splitInterpretation(text: string): string[] {
  if (!text) return []
  // 按句号、感叹号、问号分段
  const sentences = text.split(/(?<=[。！？])/)
  // 每3-4句合并为一段
  const paragraphs: string[] = []
  let current = ''
  for (let i = 0; i < sentences.length; i++) {
    current += sentences[i]
    if ((i + 1) % 3 === 0 || i === sentences.length - 1) {
      paragraphs.push(current.trim())
      current = ''
    }
  }
  return paragraphs.filter(p => p.length > 0)
}

const regenerating = ref(false)

// 查看详情
const showFortuneDetailDialog = ref(false)
const selectedFortune = ref<FortuneDetail | null>(null)
const loadingFortuneDetail = ref(false)

async function viewFortuneDetail(record: FortuneListItem) {
  showFortuneDetailDialog.value = true
  loadingFortuneDetail.value = true
  selectedFortune.value = null

  try {
    const res = await getFortuneDetail(record.id)
    if (res.success) {
      selectedFortune.value = res.data
    }
  } catch {
    ElMessage.error('加载详情失败')
  } finally {
    loadingFortuneDetail.value = false
  }
}

async function handleRegenerate() {
  regenerating.value = true
  try {
    const res = await regenerateTodayFortune()
    if (res.success) {
      todayFortune.value = res.data
      ElMessage.success('运势已重新生成')
    } else {
      ElMessage.error(res.error?.message || '重新生成失败')
    }
  } catch {
    ElMessage.error('重新生成失败，请稍后重试')
  } finally {
    regenerating.value = false
  }
}

onMounted(async () => {
  try {
    const [todayRes, listRes] = await Promise.all([
      getTodayFortune(),
      getFortuneList(),
    ])
    if (todayRes.success && todayRes.data) {
      todayFortune.value = todayRes.data
      // 使用 API 返回的时辰运势数据
      if (todayRes.data.hourly_fortunes) {
        hourlyFortunes.value = todayRes.data.hourly_fortunes
      }
    }
    if (listRes.success) {
      historyList.value = listRes.data
    }
  } catch {
    ElMessage.error('加载运势数据失败')
  } finally {
    loading.value = false
  }
})

function getScoreText(score: number): string {
  if (score >= 90) return '大吉'
  if (score >= 70) return '中吉'
  if (score >= 50) return '小吉'
  return '平'
}

function getScoreColor(score: number): string {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#eab308'
  return '#ef4444'
}

function getScoreGradient(score: number): string {
  if (score >= 80) return 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)'
  if (score >= 60) return 'linear-gradient(135deg, #eab308 0%, #ca8a04 100%)'
  return 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
}

function toggleFeedbackTag(tag: string) {
  const tags = feedbackForm.value.tags || []
  const idx = tags.indexOf(tag)
  if (idx >= 0) {
    tags.splice(idx, 1)
  } else {
    tags.push(tag)
  }
}

async function handleSubmitFeedback() {
  if (!todayFortune.value) return
  try {
    const res = await submitFortuneFeedback(todayFortune.value.id, feedbackForm.value)
    if (res.success) {
      todayFortune.value = res.data
      showFeedback.value = false
      ElMessage.success('反馈提交成功')
    }
  } catch {
    ElMessage.error('提交反馈失败')
  }
}

// 准确性标记
const markingAccuracy = ref(false)

async function handleAccuracyMark(fortuneId: number, mark: number) {
  markingAccuracy.value = true
  try {
    const res = await submitFortuneAccuracy(fortuneId, mark)
    if (res.success) {
      // 更新详情弹窗中的数据
      if (selectedFortune.value && selectedFortune.value.id === fortuneId) {
        selectedFortune.value.accuracy_mark = mark
      }
      // 更新今日运势数据
      if (todayFortune.value && todayFortune.value.id === fortuneId) {
        todayFortune.value.accuracy_mark = mark
      }
      ElMessage.success(mark === 1 ? '已标记为准确' : '已标记为不准确')
    }
  } catch {
    ElMessage.error('标记失败，请重试')
  } finally {
    markingAccuracy.value = false
  }
}
</script>

<template>
  <div class="fortune-page" v-loading="loading">
    <div class="page-header animate-fade-in">
      <h1 class="page-title">每日运势</h1>
      <p class="page-subtitle">基于八字排盘，精准推算今日运势</p>
      <el-button
        v-if="todayFortune"
        type="primary"
        :loading="regenerating"
        @click="handleRegenerate"
        class="regenerate-btn"
      >
        🔄 重新生成运势
      </el-button>
    </div>

    <!-- 今日运势卡片 -->
    <el-card v-if="todayFortune" class="today-card animate-fade-in">
      <div class="fortune-header">
        <div class="fortune-date">
          <span class="date-label">今日运势</span>
          <span class="date-value">{{ todayFortune.date }}</span>
        </div>
        <div class="fortune-score" :style="{ background: getScoreGradient(todayFortune.overall_score) }">
          <span class="score-number">{{ todayFortune.overall_score }}</span>
          <span class="score-text">{{ getScoreText(todayFortune.overall_score) }}</span>
        </div>
      </div>

      <!-- 四维评分 -->
      <div class="dimension-grid">
        <div class="dimension-item">
          <div class="dimension-icon">💼</div>
          <div class="dimension-label">事业运</div>
          <div class="dimension-score" :style="{ color: getScoreColor(todayFortune.career?.score || 0) }">
            {{ todayFortune.career?.score || 0 }}/5
          </div>
          <el-progress
            :percentage="(todayFortune.career?.score || 0) * 20"
            :color="getScoreColor(todayFortune.career?.score || 0)"
            :stroke-width="8"
          />
          <div class="dimension-desc">{{ todayFortune.career?.description || '' }}</div>
        </div>
        <div class="dimension-item">
          <div class="dimension-icon">💰</div>
          <div class="dimension-label">财运</div>
          <div class="dimension-score" :style="{ color: getScoreColor(todayFortune.wealth?.score || 0) }">
            {{ todayFortune.wealth?.score || 0 }}/5
          </div>
          <el-progress
            :percentage="(todayFortune.wealth?.score || 0) * 20"
            :color="getScoreColor(todayFortune.wealth?.score || 0)"
            :stroke-width="8"
          />
          <div class="dimension-desc">{{ todayFortune.wealth?.description || '' }}</div>
        </div>
        <div class="dimension-item">
          <div class="dimension-icon">💕</div>
          <div class="dimension-label">感情运</div>
          <div class="dimension-score" :style="{ color: getScoreColor(todayFortune.love?.score || 0) }">
            {{ todayFortune.love?.score || 0 }}/5
          </div>
          <el-progress
            :percentage="(todayFortune.love?.score || 0) * 20"
            :color="getScoreColor(todayFortune.love?.score || 0)"
            :stroke-width="8"
          />
          <div class="dimension-desc">{{ todayFortune.love?.description || '' }}</div>
        </div>
        <div class="dimension-item">
          <div class="dimension-icon">🏥</div>
          <div class="dimension-label">健康运</div>
          <div class="dimension-score" :style="{ color: getScoreColor(todayFortune.health?.score || 0) }">
            {{ todayFortune.health?.score || 0 }}/5
          </div>
          <el-progress
            :percentage="(todayFortune.health?.score || 0) * 20"
            :color="getScoreColor(todayFortune.health?.score || 0)"
            :stroke-width="8"
          />
          <div class="dimension-desc">{{ todayFortune.health?.description || '' }}</div>
        </div>
      </div>

      <!-- 幸运信息 -->
      <div class="lucky-section">
        <div class="lucky-item">
          <span class="lucky-icon">🎨</span>
          <span class="lucky-label">幸运色</span>
          <el-tag type="primary" effect="dark">{{ todayFortune.lucky_color }}</el-tag>
        </div>
        <div class="lucky-item">
          <span class="lucky-icon">🔢</span>
          <span class="lucky-label">幸运数字</span>
          <el-tag type="warning" effect="dark">{{ todayFortune.lucky_number }}</el-tag>
        </div>
        <div class="lucky-item">
          <span class="lucky-icon">🧭</span>
          <span class="lucky-label">吉利方位</span>
          <el-tag type="success" effect="dark">{{ todayFortune.lucky_direction }}</el-tag>
        </div>
      </div>

      <!-- 解读 -->
      <div class="interpretation-section">
        <h3 class="interpretation-title">🔮 运势解读</h3>
        <div class="interpretation-content">
          <div v-for="(para, idx) in splitInterpretation(todayFortune.interpretation)" :key="idx" class="interpretation-para">
            {{ para }}
          </div>
        </div>
      </div>

      <!-- 反馈按钮 -->
      <div class="feedback-section">
        <el-button @click="showFeedback = !showFeedback" class="feedback-toggle">
          {{ showFeedback ? '收起反馈' : '📝 反馈运势准确度' }}
        </el-button>

        <!-- 反馈表单 -->
        <el-card v-if="showFeedback" class="feedback-card">
          <h4>这个运势准确吗？</h4>
          <el-rate v-model="feedbackForm.rating" :max="5" class="feedback-rate" />
          <div class="feedback-tags">
            <el-tag
              v-for="tag in feedbackTags"
              :key="tag"
              :type="feedbackForm.tags?.includes(tag) ? '' : 'info'"
              class="tag-item"
              @click="toggleFeedbackTag(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
          <el-input
            v-model="feedbackForm.feedback_text"
            type="textarea"
            placeholder="补充说明（选填）"
            :rows="2"
          />
          <el-button type="primary" @click="handleSubmitFeedback" class="submit-feedback">
            提交反馈
          </el-button>
        </el-card>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-else-if="!loading" description="正在为您生成今日运势...">
      <el-button type="primary" @click="reloadPage">刷新试试</el-button>
    </el-empty>

    <!-- 时辰运势 -->
    <div class="hourly-section animate-fade-in" v-if="todayFortune && hourlyFortunes.length > 0">
      <h2 class="section-title">⏰ 时辰运势</h2>
      <p class="section-desc">每个时辰运势不同，把握吉利时段，规避不利时辰</p>
      <div class="hourly-grid">
        <div
          v-for="(item, index) in hourlyFortunes"
          :key="index"
          class="hourly-item"
          :class="{ 'current-hour': Math.floor(new Date().getHours() / 2) === index }"
        >
          <div class="hourly-header">
            <div class="hourly-icon">{{ getShichenIcon(item.shichen) }}</div>
            <div class="hourly-time-info">
              <div class="hourly-shichen">{{ item.shichen }}时</div>
              <div class="hourly-range">{{ item.shichen_range }}</div>
            </div>
            <div class="hourly-score-badge" :style="{ background: getHourlyScoreColor(item.score) }">
              {{ item.score }}分
            </div>
          </div>
          <div class="hourly-body">
            <div class="hourly-meta">
              <el-tag size="small" type="info">{{ item.ten_god }}</el-tag>
              <el-tag size="small">{{ item.element }}</el-tag>
              <span class="hourly-atmosphere">{{ item.atmosphere }}</span>
            </div>
            <div class="hourly-events">
              <div class="events-title">可能发生：</div>
              <div class="events-list">{{ item.events.join('、') }}</div>
            </div>
            <div class="hourly-actions">
              <div class="action-item favorable">
                <span class="action-icon">✅</span>
                <span class="action-label">宜：</span>
                <span class="action-text">{{ item.favorable.join('、') }}</span>
              </div>
              <div class="action-item unfavorable">
                <span class="action-icon">❌</span>
                <span class="action-label">忌：</span>
                <span class="action-text">{{ item.unfavorable.join('、') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史运势 -->
    <div class="history-section animate-fade-in" v-if="historyList.length > 0">
      <h2 class="section-title">历史运势</h2>
      <div class="history-list">
        <div
          v-for="record in historyList"
          :key="record.id"
          class="history-item"
          @click="viewFortuneDetail(record)"
        >
          <div class="history-date">
            <span class="date-day">{{ record.date.split('-')[2] }}</span>
            <span class="date-month">{{ record.date.split('-')[1] }}月</span>
          </div>
          <div class="history-content">
            <div class="history-score" :style="{ color: getScoreColor(record.overall_score) }">
              {{ record.overall_score }}分 {{ getScoreText(record.overall_score) }}
            </div>
            <div class="history-summary">{{ record.summary }}</div>
          </div>
          <div class="history-arrow">→</div>
        </div>
      </div>
    </div>

    <!-- 运势详情弹窗 -->
    <el-dialog
      v-model="showFortuneDetailDialog"
      title="运势详情"
      width="600px"
      class="detail-dialog"
    >
      <div v-if="loadingFortuneDetail" class="loading-container">加载中...</div>
      <div v-else-if="selectedFortune" class="fortune-detail-content">
        <div class="detail-header">
          <div class="detail-date">{{ selectedFortune.date }}</div>
          <div class="detail-score" :style="{ background: getScoreGradient(selectedFortune.overall_score) }">
            {{ selectedFortune.overall_score }}
          </div>
        </div>
        <el-divider />
        <div class="detail-dimensions">
          <div class="dim-item">
            <span class="dim-label">事业</span>
            <span class="dim-value">{{ selectedFortune.career?.score }}/5</span>
          </div>
          <div class="dim-item">
            <span class="dim-label">财运</span>
            <span class="dim-value">{{ selectedFortune.wealth?.score }}/5</span>
          </div>
          <div class="dim-item">
            <span class="dim-label">感情</span>
            <span class="dim-value">{{ selectedFortune.love?.score }}/5</span>
          </div>
          <div class="dim-item">
            <span class="dim-label">健康</span>
            <span class="dim-value">{{ selectedFortune.health?.score }}/5</span>
          </div>
        </div>
        <el-divider />
        <div class="detail-interpretation">
          <h4>运势解读</h4>
          <div class="interpretation-text">
            {{ selectedFortune.interpretation || '暂无解读' }}
          </div>
        </div>
        <el-divider />
        <div class="accuracy-section">
          <div class="accuracy-label">这个运势准确吗？</div>
          <div v-if="selectedFortune.accuracy_mark !== null && selectedFortune.accuracy_mark !== undefined" class="accuracy-marked">
            <el-tag :type="selectedFortune.accuracy_mark === 1 ? 'success' : 'danger'" effect="dark" size="large">
              {{ selectedFortune.accuracy_mark === 1 ? '✓ 已标记为准确' : '✗ 已标记为不准确' }}
            </el-tag>
          </div>
          <div v-else class="accuracy-buttons">
            <el-button
              type="success"
              :loading="markingAccuracy"
              @click="handleAccuracyMark(selectedFortune.id, 1)"
            >
              👍 准确
            </el-button>
            <el-button
              type="danger"
              :loading="markingAccuracy"
              @click="handleAccuracyMark(selectedFortune.id, 0)"
            >
              👎 不准确
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.fortune-page {
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

.regenerate-btn {
  margin-top: 16px;
}

/* 今日运势卡片 */
.today-card {
  margin-bottom: 32px;
}

.fortune-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--color-border);
}

.fortune-date {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.date-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.date-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
}

.fortune-score {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.score-number {
  font-size: 36px;
  font-weight: 800;
  color: white;
  line-height: 1;
}

.score-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 4px;
}

/* 四维评分 */
.dimension-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.dimension-item {
  text-align: center;
  padding: 20px;
  background: var(--color-bg-light);
  border-radius: 16px;
  border: 1px solid var(--color-border);
}

.dimension-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.dimension-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.dimension-score {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}

.dimension-desc {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 8px;
  line-height: 1.4;
}

/* 幸运信息 */
.lucky-section {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 32px;
  padding: 24px;
  background: var(--color-bg-light);
  border-radius: 16px;
}

.lucky-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lucky-icon {
  font-size: 20px;
}

.lucky-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 解读 */
.interpretation-section {
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(245, 158, 11, 0.1) 100%);
  border-radius: 16px;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.interpretation-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-accent);
}

.interpretation-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.interpretation-para {
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text);
  padding-left: 16px;
  border-left: 3px solid var(--color-primary);
}

/* 反馈 */
.feedback-section {
  text-align: center;
}

.feedback-toggle {
  margin-bottom: 16px;
}

.feedback-card {
  text-align: left;
  margin-top: 16px;
}

.feedback-card h4 {
  margin-bottom: 12px;
  color: var(--color-text);
}

.feedback-rate {
  margin-bottom: 16px;
}

.feedback-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.tag-item {
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-item:hover {
  transform: scale(1.05);
}

.submit-feedback {
  margin-top: 12px;
}

/* 历史运势 */
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

.history-date {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.date-day {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
}

.date-month {
  font-size: 12px;
  color: var(--color-text-muted);
}

.history-content {
  flex: 1;
}

.history-score {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.history-summary {
  font-size: 14px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-arrow {
  font-size: 18px;
  color: var(--color-primary);
  transition: transform 0.3s ease;
}

.history-item:hover .history-arrow {
  transform: translateX(4px);
}

/* 运势详情弹窗 */
.fortune-detail-content {
  padding: 16px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-date {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}

.detail-score {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: white;
}

.detail-dimensions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.dim-item {
  text-align: center;
  padding: 12px;
  background: var(--color-bg-light);
  border-radius: 8px;
}

.dim-label {
  display: block;
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.dim-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
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

.loading-container {
  text-align: center;
  padding: 40px;
  color: var(--color-text-secondary);
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

/* 响应式 */
@media (max-width: 768px) {
  .fortune-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .dimension-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .lucky-section {
    flex-direction: column;
    align-items: center;
  }

  .hourly-grid {
    grid-template-columns: 1fr;
  }

  .hourly-item {
    padding: 12px;
  }

  .hourly-header {
    flex-wrap: wrap;
  }
}

/* 时辰运势 */
.hourly-section {
  margin-top: 48px;
}

.section-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 24px;
}

.hourly-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.hourly-item {
  padding: 16px;
  background: var(--color-bg-light);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.hourly-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.hourly-item.current-hour {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(245, 158, 11, 0.15) 100%);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
}

.hourly-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.hourly-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.hourly-time-info {
  flex: 1;
}

.hourly-shichen {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.hourly-range {
  font-size: 12px;
  color: var(--color-text-muted);
}

.hourly-score-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.hourly-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.hourly-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.hourly-atmosphere {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.hourly-events {
  font-size: 13px;
  color: var(--color-text);
}

.events-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--color-text-secondary);
}

.events-list {
  line-height: 1.5;
}

.hourly-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.action-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  line-height: 1.5;
}

.action-icon {
  flex-shrink: 0;
}

.action-label {
  font-weight: 600;
  flex-shrink: 0;
}

.action-text {
  color: var(--color-text-secondary);
}

.favorable .action-label {
  color: #22c55e;
}

.unfavorable .action-label {
  color: #ef4444;
}
</style>
