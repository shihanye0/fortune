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

onMounted(async () => {
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
    <h1 class="page-title">占卜中心</h1>

    <!-- 选择占卜方式 -->
    <el-card class="method-card">
      <el-radio-group v-model="method">
        <el-radio-button value="liuyao">六爻占卜</el-radio-button>
        <el-radio-button value="qimen">奇门遁甲</el-radio-button>
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
          :rows="2"
        />
      </div>

      <el-button
        type="primary"
        :loading="loading"
        @click="handleSubmit"
        style="width: 100%"
      >
        {{ method === 'liuyao' ? '起卦' : '起盘' }}
      </el-button>
    </el-card>

    <!-- 结果展示 -->
    <el-card v-if="result" class="result-card">
      <template #header>
        <span>{{ method === 'liuyao' ? '卦象结果' : '奇门盘面' }}</span>
      </template>

      <div v-if="result.question" class="result-question">
        <strong>问题：</strong>{{ result.question }}
      </div>

      <el-divider />

      <div class="interpretation">
        <h3>解读</h3>
        <p>{{ result.interpretation }}</p>
      </div>

      <div class="card-actions">
        <el-button @click="showFeedback = !showFeedback">
          {{ showFeedback ? '收起反馈' : '反馈' }}
        </el-button>
      </div>

      <!-- 反馈表单 -->
      <el-card v-if="showFeedback" class="feedback-card">
        <p>这个解读准确吗？</p>
        <el-rate v-model="feedbackRating" :max="5" />
        <el-input
          v-model="feedbackText"
          type="textarea"
          placeholder="补充说明（选填）"
          :rows="2"
          style="margin-top: 12px"
        />
        <el-button type="primary" @click="handleSubmitFeedback" style="margin-top: 12px">
          提交反馈
        </el-button>
      </el-card>
    </el-card>

    <!-- 历史记录 -->
    <div class="history-section" v-if="historyList.length > 0">
      <h2>占卜历史</h2>
      <el-table :data="historyList" stripe>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'liuyao' ? '' : 'success'" size="small">
              {{ row.type === 'liuyao' ? '六爻' : '奇门' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="question" label="问题" />
        <el-table-column prop="user_rating" label="评分" width="80">
          <template #default="{ row }">
            {{ row.user_rating ? `${row.user_rating}分` : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.divination-page {
  padding: 20px 0;
}

.page-title {
  margin-bottom: 24px;
}

.method-card {
  margin-bottom: 24px;
}

.qimen-mode {
  margin-top: 16px;
}

.question-input {
  margin: 16px 0;
}

.result-card {
  margin-bottom: 24px;
}

.result-question {
  margin-bottom: 12px;
  color: var(--color-text-secondary);
}

.interpretation {
  line-height: 1.8;
}

.card-actions {
  margin-top: 16px;
  text-align: center;
}

.feedback-card {
  margin-top: 16px;
}

.history-section {
  margin-top: 32px;
}
</style>
