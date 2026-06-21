<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getTodayFortune,
  getFortuneList,
  submitFortuneFeedback,
} from '../api/fortune-api'
import type { FortuneDetail, FortuneListItem, FortuneFeedback } from '../api/fortune-api'

const loading = ref(true)
const todayFortune = ref<FortuneDetail | null>(null)
const historyList = ref<FortuneListItem[]>([])
const showFeedback = ref(false)
const feedbackForm = ref<FortuneFeedback>({ rating: 5, tags: [], feedback_text: '' })

const feedbackTags = ['很准', '一般', '不太准', '有启发', '需要更多细节']

function reloadPage() {
  window.location.reload()
}

onMounted(async () => {
  try {
    const [todayRes, listRes] = await Promise.all([
      getTodayFortune(),
      getFortuneList(),
    ])
    if (todayRes.success) {
      todayFortune.value = todayRes.data
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
</script>

<template>
  <div class="fortune-page" v-loading="loading">
    <div class="page-header animate-fade-in">
      <h1 class="page-title">每日运势</h1>
      <p class="page-subtitle">基于八字排盘，精准推算今日运势</p>
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
        <p class="interpretation-text">{{ todayFortune.interpretation }}</p>
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

    <!-- 历史运势 -->
    <div class="history-section animate-fade-in" v-if="historyList.length > 0">
      <h2 class="section-title">历史运势</h2>
      <el-table :data="historyList" stripe class="history-table">
        <el-table-column prop="date" label="日期" width="120">
          <template #default="{ row }">
            <span class="date-cell">{{ row.date }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="overall_score" label="综合评分" width="120">
          <template #default="{ row }">
            <div class="score-cell" :style="{ color: getScoreColor(row.overall_score) }">
              <span class="score-num">{{ row.overall_score }}</span>
              <span class="score-label">{{ getScoreText(row.overall_score) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="运势摘要">
          <template #default="{ row }">
            <span class="summary-cell">{{ row.summary }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
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

.interpretation-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text);
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

.history-table {
  border-radius: 12px;
  overflow: hidden;
}

.date-cell {
  font-weight: 500;
  color: var(--color-text);
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-num {
  font-size: 18px;
  font-weight: 700;
}

.score-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.summary-cell {
  color: var(--color-text-secondary);
  font-size: 14px;
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
}
</style>
