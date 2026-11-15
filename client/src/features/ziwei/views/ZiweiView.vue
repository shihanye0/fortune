<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getZiweiChart, doZiwei, getZiweiRecords, submitDivinationFeedback } from '../api/ziwei-api'
import { getDivinationDetail } from '@/features/divination/api/divination-api'
import type { ZiweiChart, DivinationRecord } from '../api/ziwei-api'

const chart = ref<ZiweiChart | null>(null)
const loadingChart = ref(false)
const chartError = ref('')
const interpreting = ref(false)
const question = ref('')
const interpretation = ref('')
const interpRecordId = ref<number | null>(null)
const historyList = ref<DivinationRecord[]>([])
const showFeedback = ref(false)
const feedbackRating = ref(5)
const feedbackText = ref('')
const feedbackRecord = ref<DivinationRecord | null>(null)

const GRID_POS: Record<string, { row: number; col: number }> = {
  寅: { row: 4, col: 1 }, 卯: { row: 3, col: 1 }, 辰: { row: 2, col: 1 }, 巳: { row: 1, col: 1 },
  午: { row: 1, col: 2 }, 未: { row: 1, col: 3 }, 申: { row: 1, col: 4 }, 酉: { row: 2, col: 4 },
  戌: { row: 3, col: 4 }, 亥: { row: 4, col: 4 }, 子: { row: 4, col: 3 }, 丑: { row: 4, col: 2 },
}
function gridStyle(branch: string) {
  const p = GRID_POS[branch]
  return { gridRow: String(p.row), gridColumn: String(p.col) }
}
function mutagenClass(m: string | null) {
  return m ? `mutagen-${m}` : ''
}
function dispName(name: string) {
  return name.endsWith('宫') ? name : name + '宫'
}
const FLOW_TAGS = ['禄', '权', '科', '忌']
function flowTag(star: string): string {
  const idx = chart.value?.flow_year?.sihua_stars?.indexOf(star) ?? -1
  return idx >= 0 ? FLOW_TAGS[idx] : ''
}

async function loadChart() {
  loadingChart.value = true
  chartError.value = ''
  try {
    const res = await getZiweiChart()
    if (res.success) chart.value = res.data
    else chartError.value = res.error?.message || '命盘加载失败'
  } catch {
    chartError.value = '网络错误，请稍后重试'
  } finally {
    loadingChart.value = false
  }
}

async function renderChart() {
  if (interpreting.value) return
  interpreting.value = true
  try {
    const res = await doZiwei({ question: question.value.trim() || undefined })
    if (res.success) {
      interpretation.value = res.data.interpretation
      interpRecordId.value = res.data.id
      chart.value = res.data as unknown as ZiweiChart
      await loadRecords()
    } else {
      ElMessage.error(res.error?.message || '解读生成失败')
    }
  } catch {
    ElMessage.error('解读超时或网络错误，请稍后重试')
  } finally {
    interpreting.value = false
  }
}

async function loadRecords() {
  try {
    const res = await getZiweiRecords()
    if (res.success) historyList.value = res.data
  } catch { /* silent */ }
}

async function loadLatestInterpretation() {
  if (!historyList.value.length || interpretation.value) return
  try {
    const res = await getDivinationDetail(historyList.value[0].id)
    if (res.success && res.data?.interpretation) {
      interpretation.value = res.data.interpretation
      interpRecordId.value = res.data.id
    }
  } catch { /* silent */ }
}

async function openFeedback(r: DivinationRecord) {
  feedbackRecord.value = r
  feedbackRating.value = r.user_rating || 5
  feedbackText.value = ''
  showFeedback.value = true
}
async function saveFeedback() {
  if (!feedbackRecord.value) return
  try {
    const res = await submitDivinationFeedback(feedbackRecord.value.id, {
      rating: feedbackRating.value,
      feedback_text: feedbackText.value || undefined,
    })
    if (res.success) {
      ElMessage.success('反馈已保存')
      showFeedback.value = false
      await loadRecords()
    }
  } catch { ElMessage.error('反馈保存失败') }
}
async function markAccuracy(record: DivinationRecord, mark: number) {
  const { default: client } = await import('@/shared/api/client')
  try {
    await client.post(`/api/v1/divination/${record.id}/accuracy`, { accuracy_mark: mark })
    ElMessage.success('已记录')
    await loadRecords()
  } catch { ElMessage.error('记录失败') }
}
onMounted(async () => { await loadRecords(); loadLatestInterpretation(); loadChart() })
</script>

<template>
  <div class="ziwei-page">
    <div class="page-header animate-fade-in">
      <h1 class="page-title">紫微斗数</h1>
      <p class="page-desc">十二宫命盘 · 基于主流排盘口径（农历正月初一换年），与 AI 解读分层</p>
    </div>
    <el-card v-if="chartError" class="error-card animate-fade-in">
      <el-result icon="warning" title="命盘暂不可用" :sub-title="chartError">
        <template #extra>
          <el-button type="primary" @click="loadChart">重试</el-button>
        </template>
      </el-result>
    </el-card>
    <el-card v-loading="loadingChart" class="chart-card animate-fade-in">
      <template #header>
        <div class="card-header">
          <span>命盘十二宫</span>
          <el-tag v-if="chart" type="info" effect="plain">{{ chart.birth.solar }} {{ chart.birth.shichen_name }} {{ chart.birth.gender }}</el-tag>
        </div>
        <div v-if="chart" class="birth-sub">
          农历 {{ chart.lunar.year_ganzhi }}年{{ chart.lunar.is_leap ? '闰' : '' }}{{ chart.lunar.month }}月{{ chart.lunar.day }}日 · {{ chart.five_elements }} · 命主{{ chart.ming_zhu }} 身主{{ chart.shen_zhu }}
        </div>
      </template>
      <div v-if="chart" class="chart-grid">
        <div v-for="p in chart.palaces" :key="p.branch" class="palace-cell" :class="{ soul: p.is_soul, body: p.is_body && !p.is_soul }" :style="gridStyle(p.branch)">
          <div class="palace-head">
            <span class="palace-name">{{ dispName(p.name) }}</span>
            <span class="palace-gz">{{ p.stem }}{{ p.branch }}</span>
          </div>
          <div class="palace-stars">
            <span v-for="s in p.major_stars" :key="s.name" class="star major" :class="mutagenClass(s.mutagen)">
              {{ s.name }}{{ s.brightness || '' }}<i v-if="s.mutagen" class="mu">{{ s.mutagen }}</i><i v-if="flowTag(s.name)" class="mu flow-mu">流{{ flowTag(s.name) }}</i>
            </span>
            <span v-for="s in p.minor_stars" :key="s.name" class="star minor">{{ s.name }}{{ s.brightness || '' }}<i v-if="s.mutagen" class="mu">{{ s.mutagen }}</i></span>
          </div>
          <div class="palace-foot">
            <span v-if="!p.major_stars.length" class="borrowed">空宫</span>
            <span class="daxian">{{ p.da_xian.start }}-{{ p.da_xian.end }}</span>
            <span v-if="p.is_soul" class="tag-soul">命</span>
            <span v-if="p.is_body" class="tag-body">身</span>
          </div>
        </div>
        <div class="center-panel">
          <div class="info-line"><span class="info-label">五行局</span><b>{{ chart.five_elements }}</b></div>
          <div class="info-line"><span class="info-label">命宫 / 身宫</span><b>{{ dispName(chart.soul_palace) }} / {{ dispName(chart.body_palace) }}</b></div>
          <div class="info-line"><span class="info-label">命主 / 身主</span><b>{{ chart.ming_zhu }} / {{ chart.shen_zhu }}</b></div>
          <div class="info-line"><span class="info-label">虚岁</span><b>{{ chart.current_age }}</b></div>
          <div class="info-line"><span class="info-label">五行局</span><b>{{ chart.five_elements }}</b></div>
          <div class="info-line"><span class="info-label">命宫 / 身宫</span><b>{{ dispName(chart.soul_palace) }} / {{ dispName(chart.body_palace) }}</b></div>
          <div class="info-line"><span class="info-label">命主 / 身主</span><b>{{ chart.ming_zhu }} / {{ chart.shen_zhu }}</b></div>
          <div class="info-line"><span class="info-label">虚岁</span><b>{{ chart.current_age }}</b></div>
          <div class="info-line"><span class="info-label">流年</span><b>{{ chart.flow_year.ganzhi }}（化禄{{ chart.flow_year.sihua_stars[0] }} 化忌{{ chart.flow_year.sihua_stars[3] }}）</b></div>
        </div>
      </div>
      <el-alert v-if="chart && chart.notes.length" :title="chart.notes.join('；')" type="info" :closable="false" class="notes-alert" />
    </el-card>
    <el-card v-if="chart?.daily" class="daily-card animate-fade-in">
      <template #header><div class="card-header"><span>今日紫微流日 · {{ chart.daily.day_ganzhi }}日</span></div></template>
      <div v-for="item in chart.daily.sihua" :key="item.type" class="daily-row">
        <span class="daily-tag" :class="'daily-' + item.type">化{{ item.type }}</span>
        <b>{{ item.star }}</b> 落 <b>{{ item.palace ? dispName(item.palace) : '不入本命盘' }}</b>
        <span v-if="item.hint" class="daily-hint"> · {{ item.hint }}</span>
      </div>
    </el-card>
    <el-card class="interp-card animate-fade-in">
      <template #header><div class="card-header"><span>AI 命盘解读</span></div></template>
      <el-input v-model="question" placeholder="想了解什么？可空，如：今年事业运如何" maxlength="120" class="q-input" />
      <el-button type="primary" :loading="interpreting" @click="renderChart" class="render-btn">
        {{ interpretation ? '重新解读' : '生成 AI 解读' }}
      </el-button>
      <div v-if="interpretation" class="interp-text">{{ interpretation }}</div>
      <div v-if="interpRecordId && interpretation" class="interp-meta">已存入占卜历史，可在下方反馈准确度</div>
    </el-card>
    <el-card class="history-card animate-fade-in">
      <template #header><div class="card-header"><span>解读历史与反馈</span></div></template>
      <el-empty v-if="!historyList.length" description="暂无解读历史" :image-size="80" />
      <div v-for="r in historyList" :key="r.id" class="history-item">
        <div class="h-top">
          <span class="h-date">{{ r.created_at?.slice(0, 10) }}</span>
          <span class="h-q">{{ r.question || '整体格局解读' }}</span>
        </div>
        <div class="h-actions">
          <el-button size="small" text type="primary" @click="openFeedback(r)">评价</el-button>
          <el-button size="small" text type="success" @click="markAccuracy(r, 1)">准</el-button>
          <el-button size="small" text type="danger" @click="markAccuracy(r, 0)">不准</el-button>
        </div>
      </div>
      <el-dialog v-model="showFeedback" title="解读反馈" width="420px">
        <el-rate v-model="feedbackRating" />
        <el-input v-model="feedbackText" type="textarea" :rows="3" placeholder="补充说明（可空）" class="fb-input" />
        <template #footer>
          <el-button @click="showFeedback = false">取消</el-button>
          <el-button type="primary" @click="saveFeedback">保存</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<style scoped>
.ziwei-page { max-width: 1080px; margin: 0 auto; padding: var(--space-4); }
.page-title { font-family: var(--font-family-display); margin: 0 0 4px; }
.page-desc { color: var(--el-text-color-secondary); margin: 0 0 16px; font-size: 14px; }
.chart-grid { display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 1fr); gap: 6px; min-height: 560px; }
.palace-cell { border: 1px solid var(--el-border-color); border-radius: 8px; padding: 8px; background: rgba(255,255,255,0.03); overflow: hidden; }
.palace-cell.soul { border-color: var(--color-primary); box-shadow: 0 0 10px rgba(99,102,241,0.25); }
.palace-cell.body { border-style: dashed; border-color: rgba(245,158,11,0.5); }
.palace-head { display: flex; justify-content: space-between; font-size: 12px; }
.palace-name { color: var(--color-accent); }
.palace-gz { color: var(--el-text-color-secondary); }
.palace-stars { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 2px 8px; min-height: 40px; }
.star { font-size: 13px; }
.star.major { color: #e2e8f0; font-weight: 600; }
.star.minor { color: #94a3b8; font-size: 12px; }
.mu { font-style: normal; margin-left: 2px; }
.mutagen-禄 { color: #22c55e; }
.mutagen-权 { color: #ef4444; }
.mutagen-科 { color: #38bdf8; }
.mutagen-忌 { color: #a78bfa; }
.flow-mu { color: #f59e0b; font-size: 10px; border: 1px solid rgba(245,158,11,0.6); border-radius: 3px; padding: 0 2px; }
.palace-foot { display: flex; align-items: center; gap: 8px; margin-top: 6px; font-size: 11px; color: var(--el-text-color-secondary); }
.borrowed { color: var(--el-text-color-secondary); font-style: italic; }
.daxian { margin-left: auto; }
.tag-soul { background: var(--color-primary); color: #fff; border-radius: 4px; padding: 0 4px; }
.tag-body { background: rgba(245,158,11,0.8); color: #1e1b4b; border-radius: 4px; padding: 0 4px; }
.center-panel { grid-row: 2 / span 2; grid-column: 2 / span 2; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; justify-content: center; gap: 10px; background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.25); }
.info-line { display: flex; gap: 12px; font-size: 14px; }
.info-label { color: var(--el-text-color-secondary); min-width: 90px; }
.notes-alert { margin-top: 12px; }
.q-input { margin-bottom: 10px; }
.render-btn { width: 100%; }
.interp-text { white-space: pre-wrap; line-height: 1.8; color: #e2e8f0; }
.interp-meta { margin-top: 8px; font-size: 12px; color: var(--el-text-color-secondary); }
.history-item { border-bottom: 1px solid var(--el-border-color-lighter); padding: 10px 0; }
.h-top { display: flex; gap: 12px; align-items: center; }
.h-date { color: var(--el-text-color-secondary); font-size: 12px; }
.h-q { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.h-actions { margin-top: 4px; }
.fb-input { margin-top: 10px; }
'.daily-card { margin-top: 16px; }
.daily-row { margin-top: 8px; font-size: 14px; }
.daily-tag { display: inline-block; padding: 1px 8px; border-radius: 999px; color: #fff; font-size: 11px; font-weight: 700; margin-right: 6px; }
.daily-禄 { background: #22c55e; }
.daily-权 { background: #ef4444; }
.daily-科 { background: #38bdf8; }
.daily-忌 { background: #a78bfa; }
.daily-hint { color: var(--el-text-color-secondary); font-size: 12px; }
@media (max-width: 640px) {
  .chart-grid { display: flex; flex-direction: column; }
  .palace-cell, .center-panel { min-height: auto; }
  .center-panel { order: -1; }
}
</style>
