<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'
import {
  getProfile,
  updateProfile,
  updateBirth,
  updatePushSettings,
  updateLLMSettings,
  testLLMConnection,
  deleteAccount,
} from '../api/profile-api'
import type { UserProfile } from '../api/profile-api'
import { getAccuracyStats } from '@/features/feedback/api/feedback-api'
import type { AccuracyStats } from '@/features/feedback/types/feedback.types'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(true)
const profile = ref<UserProfile | null>(null)
const accuracyStats = ref<AccuracyStats | null>(null)
const loadingStats = ref(false)

const editingUsername = ref(false)
const usernameForm = reactive({ username: '' })

const editingBirth = ref(false)
const birthForm = reactive({
  birth_year: 1990,
  birth_month: 1,
  birth_day: 1,
  birth_hour: 0,
  birth_minute: 0,
})

const pushForm = reactive({
  push_enabled: false,
  push_channel: 'email',
  push_time: '07:00',
  feishu_webhook: '',
})

const llmForm = reactive({
  llm_provider: '',
  llm_notes: '',
  llm_website: '',
  llm_api_key: '',
  llm_api_key_url: '',
  llm_api_url: '',
  llm_model: '',
})

const testingLLM = ref(false)
const llmTestResult = ref<{ status: string; message: string } | null>(null)

// 农历转换
import { Solar } from 'lunar-javascript'

function getLunarInfo(year: number, month: number, day: number): string {
  try {
    const solar = Solar.fromYmd(year, month, day)
    const lunar = solar.getLunar()
    return `${lunar.getMonthInChinese()}月${lunar.getDayInChinese()}`
  } catch {
    return '未知'
  }
}

// 生肖（基于农历年）
function getZodiac(year: number, month: number, day: number): string {
  try {
    const solar = Solar.fromYmd(year, month, day)
    const lunar = solar.getLunar()
    // 使用 getYearInGanZhi 获取完整的干支年，然后提取生肖
    const ganZhi = lunar.getYearInGanZhi()
    // 从干支年中提取地支，然后映射到生肖
    const dizhi = ganZhi.charAt(1) // 第二个字是地支
    const zodiacMap: Record<string, string> = {
      '子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔',
      '辰': '龙', '巳': '蛇', '午': '马', '未': '羊',
      '申': '猴', '酉': '鸡', '戌': '狗', '亥': '猪'
    }
    return zodiacMap[dizhi] || '未知'
  } catch {
    return '未知'
  }
}

// 星座（按阳历计算）
function getConstellation(month: number, day: number): string {
  // 星座日期分界（每个星座的开始日期）
  const dates = [20, 19, 21, 20, 21, 22, 23, 23, 23, 24, 22, 22]
  const signs = ['水瓶座', '双鱼座', '白羊座', '金牛座', '双子座', '巨蟹座', '狮子座', '处女座', '天秤座', '天蝎座', '射手座', '摩羯座']

  // 判断日期是否在当前星座的开始日期之前
  if (day < dates[month - 1]) {
    // 在开始日期之前，是上一个星座
    return signs[(month - 2 + 12) % 12]
  } else {
    // 在开始日期之后，是当前星座
    return signs[month - 1]
  }
}

// 时辰（精确到分钟）
function getBirthTimeText(hour: number, minute: number = 0): string {
  const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
  const hours = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时', '午时', '未时', '申时', '酉时', '戌时', '亥时']
  const shichen = hours[Math.floor(hour / 2)] || '未知'
  return `${timeStr} (${shichen})`
}

const lunarInfo = computed(() => {
  if (!profile.value?.birth_year || !profile.value?.birth_month || !profile.value?.birth_day) {
    return null
  }
  return {
    lunar: getLunarInfo(profile.value.birth_year, profile.value.birth_month, profile.value.birth_day),
    zodiac: getZodiac(profile.value.birth_year, profile.value.birth_month, profile.value.birth_day),
    constellation: getConstellation(profile.value.birth_month, profile.value.birth_day),
    timeText: getBirthTimeText(profile.value.birth_hour ?? 0, profile.value.birth_minute ?? 0),
  }
})

onMounted(async () => {
  try {
    const res = await getProfile()
    if (res.success) {
      profile.value = res.data
      usernameForm.username = res.data.username
      birthForm.birth_year = res.data.birth_year || 1990
      birthForm.birth_month = res.data.birth_month || 1
      birthForm.birth_day = res.data.birth_day || 1
      birthForm.birth_hour = res.data.birth_hour ?? 0
      birthForm.birth_minute = res.data.birth_minute ?? 0
      pushForm.push_enabled = res.data.push_enabled
      pushForm.push_channel = res.data.push_channel || 'email'
      pushForm.push_time = res.data.push_time || '07:00'
      pushForm.feishu_webhook = res.data.feishu_webhook || ''
      llmForm.llm_provider = res.data.llm_provider || 'Xiaomi MiMo'
      llmForm.llm_notes = res.data.llm_notes || ''
      llmForm.llm_website = res.data.llm_website || 'https://platform.xiaomimimo.com'
      // 脱敏的 API Key 不填回表单，避免覆盖真实 key
      llmForm.llm_api_key = (res.data.llm_api_key && !res.data.llm_api_key.includes('***')) ? res.data.llm_api_key : ''
      llmForm.llm_api_key_url = res.data.llm_api_key_url || 'https://platform.xiaomimimo.com'
      llmForm.llm_api_url = res.data.llm_api_url || 'https://token-plan-cn.xiaomimimo.com/v1'
      llmForm.llm_model = res.data.llm_model || 'mimo-v2.5'
    }
  } catch {
    ElMessage.error('加载个人信息失败')
  } finally {
    loading.value = false
  }

  // 加载准确率统计（不阻塞主页面加载）
  loadingStats.value = true
  try {
    const statsRes = await getAccuracyStats()
    if (statsRes.success) {
      accuracyStats.value = statsRes.data
    }
  } catch {
    // 准确率统计加载失败不影响页面
  } finally {
    loadingStats.value = false
  }
})

async function handleUpdateUsername() {
  try {
    const res = await updateProfile(usernameForm.username)
    if (res.success) {
      profile.value = res.data
      editingUsername.value = false
      ElMessage.success('用户名更新成功')
    }
  } catch {
    ElMessage.error('更新失败')
  }
}

async function handleUpdateBirth() {
  try {
    const res = await updateBirth(birthForm)
    if (res.success) {
      profile.value = res.data
      editingBirth.value = false
      ElMessage.success('生辰信息更新成功')
    }
  } catch {
    ElMessage.error('更新失败')
  }
}

async function handleUpdatePushSettings() {
  try {
    const res = await updatePushSettings(pushForm)
    if (res.success) {
      profile.value = res.data
      ElMessage.success('推送设置更新成功')
    }
  } catch {
    ElMessage.error('更新失败')
  }
}

async function handleUpdateLLMSettings() {
  try {
    const res = await updateLLMSettings(llmForm)
    if (res.success) {
      profile.value = res.data
      ElMessage.success('LLM配置更新成功')
    }
  } catch {
    ElMessage.error('更新失败')
  }
}

async function handleTestLLM() {
  testingLLM.value = true
  llmTestResult.value = null
  try {
    const res = await testLLMConnection({
      llm_api_key: llmForm.llm_api_key || undefined,
      llm_api_url: llmForm.llm_api_url || undefined,
      llm_model: llmForm.llm_model || undefined,
    })
    if (res.success) {
      llmTestResult.value = { status: 'success', message: res.data.message }
      ElMessage.success('连接测试成功')
    } else {
      llmTestResult.value = { status: 'error', message: res.error?.message || '连接失败' }
      ElMessage.error('连接测试失败')
    }
  } catch {
    llmTestResult.value = { status: 'error', message: '请求异常，请检查网络' }
    ElMessage.error('连接测试失败')
  } finally {
    testingLLM.value = false
  }
}

function getAccuracyColor(rate: number): string {
  if (rate >= 80) return '#22c55e'
  if (rate >= 60) return '#eab308'
  return '#ef4444'
}

function getDimensionLabel(key: string): string {
  const labels: Record<string, string> = {
    career: '事业',
    wealth: '财运',
    love: '感情',
    health: '健康',
  }
  return labels[key] || key
}

function getDimensionIcon(key: string): string {
  const icons: Record<string, string> = {
    career: '💼',
    wealth: '💰',
    love: '💕',
    health: '🏥',
  }
  return icons[key] || '📊'
}

async function handleDeleteAccount() {
  try {
    const { value: password } = await ElMessageBox.prompt('请输入密码确认注销', '注销账号', {
      confirmButtonText: '确认注销',
      cancelButtonText: '取消',
      inputType: 'password',
      type: 'warning',
    })
    if (password) {
      const res = await deleteAccount(password)
      if (res.success) {
        authStore.logout()
        ElMessage.success('账号已注销')
        router.push('/')
      }
    }
  } catch {
    // user cancelled
  }
}
</script>

<template>
  <div class="profile-page" v-loading="loading">
    <div class="page-header animate-fade-in">
      <h1 class="page-title">个人中心</h1>
      <p class="page-subtitle">管理您的个人信息和推送设置</p>
    </div>

    <template v-if="profile">
      <!-- 基本信息 -->
      <el-card class="section-card animate-fade-in">
        <template #header>
          <div class="card-header">
            <div class="card-title">
              <span class="card-icon">👤</span>
              <span>基本信息</span>
            </div>
            <el-button text @click="editingUsername = !editingUsername" class="edit-btn">
              {{ editingUsername ? '取消' : '编辑' }}
            </el-button>
          </div>
        </template>
        <div v-if="!editingUsername" class="info-grid">
          <div class="info-item">
            <span class="info-label">用户名</span>
            <span class="info-value">{{ profile.username }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">邮箱</span>
            <span class="info-value">{{ profile.email }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">注册时间</span>
            <span class="info-value">{{ new Date(profile.created_at).toLocaleDateString('zh-CN') }}</span>
          </div>
        </div>
        <div v-else class="edit-form">
          <el-input v-model="usernameForm.username" placeholder="新用户名" />
          <el-button type="primary" @click="handleUpdateUsername" class="save-btn">保存</el-button>
        </div>
      </el-card>

      <!-- 生辰信息 -->
      <el-card class="section-card animate-fade-in">
        <template #header>
          <div class="card-header">
            <div class="card-title">
              <span class="card-icon">🌙</span>
              <span>生辰信息</span>
            </div>
            <el-button text @click="editingBirth = !editingBirth" class="edit-btn">
              {{ editingBirth ? '取消' : '修改生辰' }}
            </el-button>
          </div>
        </template>
        <div v-if="!editingBirth">
          <div class="birth-info-grid">
            <div class="birth-card">
              <div class="birth-label">阳历生日</div>
              <div class="birth-value">
                {{ profile.birth_year }}年{{ profile.birth_month }}月{{ profile.birth_day }}日
              </div>
              <div class="birth-detail">{{ getBirthTimeText(profile.birth_hour ?? 0, profile.birth_minute ?? 0) }}</div>
            </div>
            <div class="birth-card lunar">
              <div class="birth-label">农历生日</div>
              <div class="birth-value" v-if="lunarInfo">
                {{ lunarInfo.lunar }}
              </div>
              <div class="birth-detail" v-if="lunarInfo">
                {{ lunarInfo.zodiac }}年 · {{ lunarInfo.constellation }}
              </div>
            </div>
          </div>
        </div>
        <div v-else class="edit-form">
          <el-form label-width="80px">
            <el-form-item label="年">
              <el-input-number v-model="birthForm.birth_year" :min="1900" :max="2100" style="width: 100%" />
            </el-form-item>
            <el-form-item label="月">
              <el-input-number v-model="birthForm.birth_month" :min="1" :max="12" style="width: 100%" />
            </el-form-item>
            <el-form-item label="日">
              <el-input-number v-model="birthForm.birth_day" :min="1" :max="31" style="width: 100%" />
            </el-form-item>
            <el-form-item label="出生时间">
              <div style="display: flex; gap: 12px; width: 100%">
                <el-select v-model="birthForm.birth_hour" placeholder="时" style="flex: 1">
                  <el-option v-for="h in 24" :key="h-1" :label="`${h-1}时`" :value="h-1" />
                </el-select>
                <el-select v-model="birthForm.birth_minute" placeholder="分" style="flex: 1">
                  <el-option v-for="m in 12" :key="(m-1)*5" :label="`${String((m-1)*5).padStart(2, '0')}分`" :value="(m-1)*5" />
                </el-select>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdateBirth">保存</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>

      <!-- 推送设置 -->
      <el-card class="section-card animate-fade-in">
        <template #header>
          <div class="card-title">
            <span class="card-icon">🔔</span>
            <span>推送设置</span>
          </div>
        </template>
        <el-form label-width="100px" class="push-form">
          <el-form-item label="每日推送">
            <el-switch v-model="pushForm.push_enabled" active-text="开启" inactive-text="关闭" />
          </el-form-item>
          <el-form-item label="推送渠道">
            <el-radio-group v-model="pushForm.push_channel">
              <el-radio value="email">QQ邮箱</el-radio>
              <el-radio value="feishu">飞书</el-radio>
              <el-radio value="both">两者</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="推送时间">
            <el-time-picker v-model="pushForm.push_time" format="HH:mm" value-format="HH:mm" />
          </el-form-item>
          <el-form-item v-if="pushForm.push_channel !== 'email'" label="飞书 Webhook">
            <el-input v-model="pushForm.feishu_webhook" placeholder="飞书机器人 Webhook URL" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleUpdatePushSettings">保存设置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- LLM 配置 -->
      <el-card class="section-card animate-fade-in llm-card">
        <template #header>
          <div class="card-header">
            <div class="card-title">
              <span class="card-icon">🤖</span>
              <span>LLM 配置</span>
            </div>
            <el-tag v-if="llmForm.llm_provider" type="success" effect="plain" size="small">
              {{ llmForm.llm_provider }}
            </el-tag>
          </div>
        </template>
        <el-form label-width="100px" class="llm-form">
          <!-- 供应商名称 + 备注 -->
          <div class="llm-row">
            <el-form-item label="供应商名称" class="llm-row-main">
              <el-input v-model="llmForm.llm_provider" placeholder="例如：Xiaomi MiMo、DeepSeek" />
            </el-form-item>
            <el-form-item label="备注" class="llm-row-sub">
              <el-input v-model="llmForm.llm_notes" placeholder="例如：公司专用账号" />
            </el-form-item>
          </div>

          <!-- 官网链接 -->
          <el-form-item label="官网链接">
            <el-input v-model="llmForm.llm_website" placeholder="https://platform.xiaomimimo.com">
              <template #prefix>
                <span>🔗</span>
              </template>
              <template #append>
                <el-button @click="llmForm.llm_website && window.open(llmForm.llm_website, '_blank')">
                  访问
                </el-button>
              </template>
            </el-input>
          </el-form-item>

          <!-- API Key + 获取链接 -->
          <el-form-item label="API Key">
            <el-input v-model="llmForm.llm_api_key" type="password" placeholder="留空则使用服务器默认配置" show-password>
              <template #prefix>
                <span>🔑</span>
              </template>
            </el-input>
            <div class="llm-hint" v-if="llmForm.llm_api_key_url">
              <el-link type="primary" :href="llmForm.llm_api_key_url" target="_blank" :underline="false">
                获取 API Key →
              </el-link>
            </div>
          </el-form-item>

          <!-- 请求地址 -->
          <el-form-item label="请求地址">
            <el-input v-model="llmForm.llm_api_url" placeholder="https://token-plan-cn.xiaomimimo.com/v1">
              <template #prefix>
                <span>🌐</span>
              </template>
            </el-input>
            <div class="llm-hint">完整 URL：{{ llmForm.llm_api_url || '...' }}/chat/completions</div>
          </el-form-item>

          <!-- 模型名称 -->
          <el-form-item label="模型名称">
            <el-input v-model="llmForm.llm_model" placeholder="mimo-v2.5">
              <template #prefix>
                <span>🧠</span>
              </template>
            </el-input>
          </el-form-item>

          <!-- 测试结果 -->
          <div v-if="llmTestResult" class="llm-test-result" :class="llmTestResult.status">
            <span v-if="llmTestResult.status === 'success'">✅</span>
            <span v-else>❌</span>
            {{ llmTestResult.message }}
          </div>

          <!-- 操作按钮 -->
          <el-form-item>
            <div class="llm-actions">
              <el-button type="primary" @click="handleUpdateLLMSettings">保存配置</el-button>
              <el-button @click="handleTestLLM" :loading="testingLLM">
                🔌 测试连接
              </el-button>
            </div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 预测准确率 -->
      <el-card class="section-card animate-fade-in" v-if="accuracyStats">
        <template #header>
          <div class="card-title">
            <span class="card-icon">📊</span>
            <span>预测准确率</span>
          </div>
        </template>
        <div class="accuracy-cards">
          <div class="accuracy-card fortune-card">
            <div class="accuracy-card-header">
              <span class="accuracy-card-icon">🔮</span>
              <span class="accuracy-card-title">运势准确率</span>
            </div>
            <div class="accuracy-card-body">
              <div class="accuracy-big-number" :style="{ color: getAccuracyColor(accuracyStats.fortune_accuracy.rate) }">
                {{ accuracyStats.fortune_accuracy.rate }}%
              </div>
              <el-progress
                :percentage="accuracyStats.fortune_accuracy.rate"
                :color="getAccuracyColor(accuracyStats.fortune_accuracy.rate)"
                :stroke-width="10"
              />
              <div class="accuracy-detail">
                <span>总数：{{ accuracyStats.fortune_accuracy.total }}</span>
                <span>准确：{{ accuracyStats.fortune_accuracy.accurate }}</span>
              </div>
            </div>
          </div>
          <div class="accuracy-card divination-card">
            <div class="accuracy-card-header">
              <span class="accuracy-card-icon">☯</span>
              <span class="accuracy-card-title">占卜准确率</span>
            </div>
            <div class="accuracy-card-body">
              <div class="accuracy-big-number" :style="{ color: getAccuracyColor(accuracyStats.divination_accuracy.rate) }">
                {{ accuracyStats.divination_accuracy.rate }}%
              </div>
              <el-progress
                :percentage="accuracyStats.divination_accuracy.rate"
                :color="getAccuracyColor(accuracyStats.divination_accuracy.rate)"
                :stroke-width="10"
              />
              <div class="accuracy-detail">
                <span>总数：{{ accuracyStats.divination_accuracy.total }}</span>
                <span>准确：{{ accuracyStats.divination_accuracy.accurate }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="dimension-accuracy" v-if="Object.keys(accuracyStats.dimension_accuracy).length > 0">
          <h4 class="dimension-title">各维度准确率</h4>
          <div class="dimension-list">
            <div
              v-for="(stat, key) in accuracyStats.dimension_accuracy"
              :key="key"
              class="dimension-item"
            >
              <div class="dimension-info">
                <span class="dimension-icon">{{ getDimensionIcon(String(key)) }}</span>
                <span class="dimension-name">{{ getDimensionLabel(String(key)) }}</span>
              </div>
              <div class="dimension-progress">
                <el-progress
                  :percentage="stat.rate"
                  :color="getAccuracyColor(stat.rate)"
                  :stroke-width="8"
                />
              </div>
              <div class="dimension-stats">
                <span class="dimension-rate" :style="{ color: getAccuracyColor(stat.rate) }">{{ stat.rate }}%</span>
                <span class="dimension-count">({{ stat.accurate }}/{{ stat.total }})</span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 危险操作 -->
      <el-card class="section-card danger-card animate-fade-in">
        <template #header>
          <div class="card-title">
            <span class="card-icon">⚠️</span>
            <span>危险操作</span>
          </div>
        </template>
        <div class="danger-content">
          <div class="danger-info">
            <h4>注销账号</h4>
            <p>注销后，您的所有数据将被永久删除，且无法恢复。</p>
          </div>
          <el-button type="danger" @click="handleDeleteAccount">注销账号</el-button>
        </div>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.profile-page {
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
.section-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}

.card-icon {
  font-size: 24px;
}

.edit-btn {
  color: var(--color-primary) !important;
}

/* 信息网格 */
.info-grid {
  display: grid;
  gap: 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--color-bg-light);
  border-radius: 12px;
}

.info-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.info-value {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text);
}

/* 生辰信息 */
.birth-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.birth-card {
  padding: 24px;
  background: linear-gradient(135deg, var(--color-bg-light) 0%, var(--color-surface) 100%);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  text-align: center;
  transition: all 0.3s ease;
}

.birth-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
}

.birth-card.lunar {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-color: rgba(245, 158, 11, 0.3);
}

.birth-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.birth-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  font-family: var(--font-family-display);
  margin-bottom: 8px;
}

.birth-detail {
  font-size: 14px;
  color: var(--color-accent);
}

/* 编辑表单 */
.edit-form {
  padding: 16px 0;
}

.save-btn {
  margin-top: 16px;
}

/* 推送设置 */
.push-form {
  max-width: 500px;
}

/* LLM 配置 */
.llm-form {
  max-width: 600px;
}

.llm-row {
  display: flex;
  gap: 16px;
}

.llm-row-main {
  flex: 1;
}

.llm-row-sub {
  flex: 1;
}

.llm-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.llm-test-result {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.llm-test-result.success {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
}

.llm-test-result.error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.llm-actions {
  display: flex;
  gap: 12px;
}

/* 危险操作 */
.danger-card {
  border-color: rgba(239, 68, 68, 0.3) !important;
}

/* 预测准确率 */
.accuracy-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.accuracy-card {
  padding: 24px;
  background: linear-gradient(135deg, var(--color-bg-light) 0%, var(--color-surface) 100%);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.accuracy-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
}

.fortune-card {
  border-left: 4px solid #8b5cf6;
}

.divination-card {
  border-left: 4px solid #06b6d4;
}

.accuracy-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.accuracy-card-icon {
  font-size: 24px;
}

.accuracy-card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.accuracy-card-body {
  text-align: center;
}

.accuracy-big-number {
  font-size: 36px;
  font-weight: 800;
  font-family: var(--font-family-display);
  margin-bottom: 12px;
}

.accuracy-detail {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 维度准确率 */
.dimension-accuracy {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border);
}

.dimension-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 16px;
}

.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dimension-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--color-bg-light);
  border-radius: 12px;
}

.dimension-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 80px;
}

.dimension-info .dimension-icon {
  font-size: 20px;
}

.dimension-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.dimension-progress {
  flex: 1;
}

.dimension-stats {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 80px;
  justify-content: flex-end;
}

.dimension-rate {
  font-size: 16px;
  font-weight: 700;
}

.dimension-count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.danger-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.danger-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #ef4444;
  margin-bottom: 4px;
}

.danger-info p {
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 响应式 */
@media (max-width: 768px) {
  .birth-info-grid {
    grid-template-columns: 1fr;
  }

  .danger-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }

  .accuracy-cards {
    grid-template-columns: 1fr;
  }

  .llm-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
