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
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
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
    <h1 class="page-title">每日运势</h1>

    <!-- 今日运势卡片 -->
    <el-card v-if="todayFortune" class="today-card">
      <template #header>
        <div class="card-header">
          <span>今日运势</span>
          <span class="date">{{ todayFortune.date }}</span>
        </div>
      </template>

      <div class="score-section">
        <div class="overall-score" :style="{ color: getScoreColor(todayFortune.overall_score) }">
          <span class="score-number">{{ todayFortune.overall_score }}</span>
          <span class="score-text">{{ getScoreText(todayFortune.overall_score) }}</span>
        </div>
      </div>

      <el-row :gutter="16" class="dimension-scores">
        <el-col :span="6">
          <div class="dimension">
            <span class="dim-label">事业</span>
            <el-progress :percentage="todayFortune.career" :color="getScoreColor(todayFortune.career)" />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="dimension">
            <span class="dim-label">财运</span>
            <el-progress :percentage="todayFortune.wealth" :color="getScoreColor(todayFortune.wealth)" />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="dimension">
            <span class="dim-label">感情</span>
            <el-progress :percentage="todayFortune.love" :color="getScoreColor(todayFortune.love)" />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="dimension">
            <span class="dim-label">健康</span>
            <el-progress :percentage="todayFortune.health" :color="getScoreColor(todayFortune.health)" />
          </div>
        </el-col>
      </el-row>

      <div class="lucky-info">
        <span>幸运色：<el-tag size="small">{{ todayFortune.lucky_color }}</el-tag></span>
        <span>幸运数字：<el-tag size="small">{{ todayFortune.lucky_number }}</el-tag></span>
        <span>吉利方位：<el-tag size="small">{{ todayFortune.lucky_direction }}</el-tag></span>
      </div>

      <el-divider />
      <div class="interpretation">
        <p>{{ todayFortune.interpretation }}</p>
      </div>

      <div class="card-actions">
        <el-button @click="showFeedback = !showFeedback">
          {{ showFeedback ? '收起反馈' : '反馈' }}
        </el-button>
      </div>

      <!-- 反馈表单 -->
      <el-card v-if="showFeedback" class="feedback-card">
        <p>这个运势准确吗？</p>
        <el-rate v-model="feedbackForm.rating" :max="5" />
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
        <el-button type="primary" @click="handleSubmitFeedback" style="margin-top: 12px">
          提交反馈
        </el-button>
      </el-card>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-else-if="!loading" description="今日运势正在生成中，请稍后查看" />

    <!-- 历史运势 -->
    <div class="history-section" v-if="historyList.length > 0">
      <h2>历史运势</h2>
      <el-table :data="historyList" stripe>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="overall_score" label="综合评分" width="100">
          <template #default="{ row }">
            <span :style="{ color: getScoreColor(row.overall_score) }">{{ row.overall_score }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" />
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.fortune-page {
  padding: 20px 0;
}

.page-title {
  margin-bottom: 24px;
}

.today-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.score-section {
  text-align: center;
  margin-bottom: 24px;
}

.overall-score {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
}

.score-number {
  font-size: 48px;
  font-weight: bold;
}

.score-text {
  font-size: 18px;
  margin-top: 4px;
}

.dimension-scores {
  margin-bottom: 16px;
}

.dimension {
  text-align: center;
}

.dim-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.lucky-info {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin: 16px 0;
}

.interpretation {
  line-height: 1.8;
  color: var(--color-text);
}

.card-actions {
  margin-top: 16px;
  text-align: center;
}

.feedback-card {
  margin-top: 16px;
}

.feedback-tags {
  margin: 12px 0;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-item {
  cursor: pointer;
}

.history-section {
  margin-top: 32px;
}
</style>
