<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'
import {
  getProfile,
  getBaziProfile,
  updateProfile,
  updateBirth,
  updatePushSettings,
  updateLLMSettings,
  testLLMConnection,
  deleteAccount,
} from '../api/profile-api'
import type { BaziProfile, UserProfile } from '../api/profile-api'
import { getAccuracyStats } from '@/features/feedback/api/feedback-api'
import type { AccuracyStats } from '@/features/feedback/types/feedback.types'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(true)
const profile = ref<UserProfile | null>(null)
const accuracyStats = ref<AccuracyStats | null>(null)
const loadingStats = ref(false)
const baziProfile = ref<BaziProfile | null>(null)
const loadingBaziProfile = ref(false)
const fiveElementOrder = ['木', '火', '土', '金', '水']

const editingUsername = ref(false)
const usernameForm = reactive({ username: '' })

const editingBirth = ref(false)
const birthForm = reactive({
  birth_year: 1990,
  birth_month: 1,
  birth_day: 1,
  birth_hour: 0,
  gender: 1,
  birth_location: '',
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

const defaultLLMConfig = {
  provider: 'DeepSeek',
  website: 'https://platform.deepseek.com',
  apiKeyUrl: 'https://platform.deepseek.com/api_keys',
  apiUrl: 'https://api.deepseek.com',
  model: 'deepseek-flash',
}
const llmConfigSource = ref<'personal' | 'server_default'>('server_default')
const usesServerDefaultLLM = computed(() => llmConfigSource.value === 'server_default')

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

// 当前后端只保存整点，按小时映射时辰。
function getBirthTimeText(hour: number): string {
  const timeStr = `${String(hour).padStart(2, '0')}:00`
  const hours = ['子时', '丑时', '寅时', '卯时', '辰时', '巳时', '午时', '未时', '申时', '酉时', '戌时', '亥时']
  const shichen = hours[Math.floor(hour / 2)] || '未知'
  return `${timeStr} (${shichen})`
}

function normalizeLLMApiUrl(url: string | null | undefined): string {
  const cleaned = url?.trim()
  return cleaned || defaultLLMConfig.apiUrl
}

function hydrateLLMForm(nextProfile: UserProfile) {
  llmConfigSource.value = nextProfile.llm_config_source || 'server_default'
  llmForm.llm_provider = nextProfile.llm_provider || defaultLLMConfig.provider
  llmForm.llm_notes = nextProfile.llm_notes || ''
  llmForm.llm_website = nextProfile.llm_website || defaultLLMConfig.website
  // 脱敏的 API Key 不填回表单，避免覆盖真实 key
  llmForm.llm_api_key = (
    nextProfile.llm_api_key && !nextProfile.llm_api_key.includes('***')
  ) ? nextProfile.llm_api_key : ''
  llmForm.llm_api_key_url = nextProfile.llm_api_key_url || defaultLLMConfig.apiKeyUrl
  llmForm.llm_api_url = normalizeLLMApiUrl(nextProfile.llm_api_url)
  llmForm.llm_model = nextProfile.llm_model || defaultLLMConfig.model
}

const lunarInfo = computed(() => {
  if (!profile.value?.birth_year || !profile.value?.birth_month || !profile.value?.birth_day) {
    return null
  }
  return {
    lunar: getLunarInfo(profile.value.birth_year, profile.value.birth_month, profile.value.birth_day),
    zodiac: getZodiac(profile.value.birth_year, profile.value.birth_month, profile.value.birth_day),
    constellation: getConstellation(profile.value.birth_month, profile.value.birth_day),
    timeText: getBirthTimeText(profile.value.birth_hour ?? 0),
  }
})

async function loadBaziProfile() {
  loadingBaziProfile.value = true
  try {
    const baziRes = await getBaziProfile()
    baziProfile.value = baziRes.success ? baziRes.data : null
  } catch {
    // 生辰资料不完整或临时网络问题时，不阻塞个人中心。
    baziProfile.value = null
  } finally {
    loadingBaziProfile.value = false
  }
}

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
      birthForm.gender = res.data.gender ?? 1
      birthForm.birth_location = res.data.birth_location || ''
      pushForm.push_enabled = res.data.push_enabled
      pushForm.push_channel = res.data.push_channel || 'email'
      pushForm.push_time = res.data.push_time || '07:00'
      pushForm.feishu_webhook = res.data.feishu_webhook || ''
      hydrateLLMForm(res.data)
    }
  } catch {
    ElMessage.error('加载个人信息失败')
  } finally {
    loading.value = false
  }

  // 命盘数据独立加载，失败不影响个人资料与设置。
  await loadBaziProfile()

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
      await loadBaziProfile()
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
      hydrateLLMForm(res.data)
      ElMessage.success('LLM配置更新成功')
    }
  } catch {
    ElMessage.error('更新失败')
  }
}

async function handleUseServerDefaultLLM() {
  try {
    await ElMessageBox.confirm(
      '将清除当前账户保存的 LLM 地址、模型与 API Key，之后改用服务器已保存的 DeepSeek 配置。此操作不会测试或显示服务器 Key。',
      '切换到服务器 DeepSeek',
      { confirmButtonText: '切换', cancelButtonText: '取消', type: 'warning' },
    )
    const res = await updateLLMSettings({ use_server_default: true })
    if (res.success) {
      profile.value = res.data
      hydrateLLMForm(res.data)
      llmTestResult.value = null
      ElMessage.success('已切换到服务器默认 DeepSeek')
    }
  } catch {
    // 用户取消时不提示错误。
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

function openLLMWebsite() {
  if (llmForm.llm_website) {
    window.open(llmForm.llm_website, '_blank')
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

function fiveElementPercentage(value: number): number {
  const total = baziProfile.value
    ? Object.values(baziProfile.value.five_elements).reduce((sum, count) => sum + count, 0)
    : 0
  return total ? Math.round((value / total) * 100) : 0
}

function isCurrentLuckCycle(startYear: number, endYear: number): boolean {
  const currentYear = new Date().getFullYear()
  return currentYear >= startYear && currentYear <= endYear
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
              <div class="birth-detail">{{ getBirthTimeText(profile.birth_hour ?? 0) }}</div>
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
            <div class="birth-card">
              <div class="birth-label">排盘资料</div>
              <div class="birth-value">{{ profile.gender === 0 ? '女' : '男' }}</div>
              <div class="birth-detail">出生地：{{ profile.birth_location || '未填写（当前不参与真太阳时校正）' }}</div>
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
            <el-form-item label="出生时辰">
              <el-select v-model="birthForm.birth_hour" placeholder="时" style="width: 100%">
                <el-option v-for="h in 24" :key="h-1" :label="`${h-1}:00`" :value="h-1" />
              </el-select>
            </el-form-item>
            <el-form-item label="性别">
              <el-radio-group v-model="birthForm.gender">
                <el-radio :value="1">男</el-radio>
                <el-radio :value="0">女</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="出生地">
              <el-input
                v-model="birthForm.birth_location"
                name="birth-location"
                autocomplete="address-level2"
                placeholder="选填；当前不参与真太阳时校正"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdateBirth">保存</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>

      <!-- 命盘基础：让排盘依据对用户可见 -->
      <el-card class="section-card bazi-card animate-fade-in" v-loading="loadingBaziProfile">
        <template #header>
          <div class="card-header">
            <div class="card-title">
              <span class="card-icon">☷</span>
              <span>命盘基础</span>
            </div>
            <el-tag v-if="baziProfile" effect="plain" class="day-master-tag">
              日主 · {{ baziProfile.day_master }}
            </el-tag>
          </div>
        </template>

        <template v-if="baziProfile">
          <div class="bazi-intro">
            <div>
              <span class="bazi-kicker">PERSONAL CHART</span>
              <p>四柱与大运是每日参考的计算基础，展开后可核对每一项，而不只看到结论。</p>
            </div>
            <div class="favorable-elements">
              <span>基础偏向</span>
              <el-tag v-for="element in baziProfile.favorable_elements" :key="element" effect="dark" type="warning">
                {{ element }}
              </el-tag>
            </div>
          </div>

          <div class="pillar-grid" aria-label="四柱命盘">
            <div v-for="pillar in baziProfile.pillars" :key="pillar.key" class="pillar-item">
              <span class="pillar-label">{{ pillar.label }}</span>
              <strong class="pillar-value">{{ pillar.pillar }}</strong>
              <span class="pillar-ten-god">{{ pillar.ten_god }}</span>
            </div>
          </div>

          <div class="bazi-detail-grid">
            <section class="bazi-subsection">
              <div class="subsection-heading">
                <span>五行分布</span>
                <small>四柱可见字</small>
              </div>
              <div class="element-list">
                <div v-for="element in fiveElementOrder" :key="element" class="element-row">
                  <span class="element-name">{{ element }}</span>
                  <div class="element-track" aria-hidden="true">
                    <span
                      class="element-fill"
                      :class="`element-${element}`"
                      :style="{ width: `${fiveElementPercentage(baziProfile.five_elements[element] || 0)}%` }"
                    />
                  </div>
                  <span class="element-count">{{ baziProfile.five_elements[element] || 0 }}</span>
                </div>
              </div>
            </section>

            <section class="bazi-subsection luck-subsection">
              <div class="subsection-heading">
                <span>大运区间</span>
                <small>按节气差起运</small>
              </div>
              <div class="luck-cycle-list">
                <div
                  v-for="cycle in baziProfile.major_luck_cycles"
                  :key="`${cycle.start_year}-${cycle.pillar}`"
                  class="luck-cycle"
                  :class="{ 'is-current': isCurrentLuckCycle(cycle.start_year, cycle.end_year) }"
                >
                  <span class="luck-cycle-age">{{ cycle.start_age }}–{{ cycle.end_age }} 岁</span>
                  <strong>{{ cycle.pillar }}</strong>
                  <span class="luck-cycle-year">{{ cycle.start_year }}–{{ cycle.end_year }}</span>
                </div>
              </div>
            </section>
          </div>

          <div class="bazi-notes">
            <p><span>计算口径</span>{{ baziProfile.calculation_note }}</p>
            <p><span>使用提示</span>{{ baziProfile.usage_notice }}</p>
          </div>
        </template>

        <el-empty v-else-if="!loadingBaziProfile" description="暂无法生成命盘，请检查生辰信息" :image-size="72" />
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
            <el-tag :type="usesServerDefaultLLM ? 'primary' : 'success'" effect="plain" size="small">
              {{ usesServerDefaultLLM ? '服务器默认 · DeepSeek' : llmForm.llm_provider }}
            </el-tag>
          </div>
        </template>
        <el-form label-width="100px" class="llm-form">
          <div class="llm-source-banner" :class="{ 'is-server-default': usesServerDefaultLLM }">
            <div class="llm-source-copy">
              <span class="llm-source-kicker">CURRENT SOURCE</span>
              <strong>{{ usesServerDefaultLLM ? '服务器默认 DeepSeek' : '个人 LLM 覆盖配置' }}</strong>
              <p v-if="usesServerDefaultLLM">请求将使用服务器已保存的 DeepSeek Key、地址与模型；Key 不会显示在页面上。</p>
              <p v-else>当前账户保存了独立配置，它会优先于服务器默认值。切换前会先清除这组个人覆盖项。</p>
            </div>
            <el-button
              v-if="!usesServerDefaultLLM"
              plain
              type="primary"
              @click="handleUseServerDefaultLLM"
            >
              使用服务器 DeepSeek
            </el-button>
          </div>

          <!-- 供应商名称 + 备注 -->
          <div class="llm-row">
            <el-form-item label="供应商名称" class="llm-row-main">
              <el-input v-model="llmForm.llm_provider" name="llm-provider" autocomplete="off" placeholder="例如：DeepSeek" />
            </el-form-item>
            <el-form-item label="备注" class="llm-row-sub">
              <el-input v-model="llmForm.llm_notes" name="llm-notes" autocomplete="off" placeholder="例如：公司专用账号" />
            </el-form-item>
          </div>

          <!-- 官网链接 -->
          <el-form-item label="官网链接">
            <el-input v-model="llmForm.llm_website" name="llm-website" type="url" autocomplete="off" spellcheck="false" placeholder="https://platform.deepseek.com">
              <template #prefix>
                <span>🔗</span>
              </template>
              <template #append>
                <el-button @click="openLLMWebsite">
                  访问
                </el-button>
              </template>
            </el-input>
          </el-form-item>

          <!-- API Key + 获取链接 -->
          <el-form-item label="API Key">
            <el-input v-model="llmForm.llm_api_key" name="llm-api-key" type="password" autocomplete="off" spellcheck="false" placeholder="留空则使用服务器默认配置" show-password>
              <template #prefix>
                <span>🔑</span>
              </template>
            </el-input>
            <div class="llm-hint" v-if="usesServerDefaultLLM">
              当前不使用个人 Key；如要改为个人配置，填写 Key 后保存即可。
            </div>
            <div class="llm-hint" v-else-if="llmForm.llm_api_key_url">
              <el-link type="primary" :href="llmForm.llm_api_key_url" target="_blank" :underline="false">
                获取 API Key →
              </el-link>
            </div>
          </el-form-item>

          <!-- 请求地址 -->
          <el-form-item label="请求地址">
            <el-input v-model="llmForm.llm_api_url" name="llm-api-url" type="url" autocomplete="off" spellcheck="false" placeholder="https://api.deepseek.com">
              <template #prefix>
                <span>🌐</span>
              </template>
            </el-input>
            <div class="llm-hint">完整 URL：{{ llmForm.llm_api_url || '…' }}/chat/completions</div>
          </el-form-item>

          <!-- 模型名称 -->
          <el-form-item label="模型名称">
            <el-input v-model="llmForm.llm_model" name="llm-model" autocomplete="off" spellcheck="false" placeholder="deepseek-flash">
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
  min-width: 0;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-light);
  border-radius: 12px;
}

.info-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.info-value {
  min-width: 0;
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text);
  overflow-wrap: anywhere;
  text-align: right;
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
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
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

/* 命盘基础：以“档案册”式层级呈现可核对的计算依据。 */
.bazi-card {
  overflow: hidden;
  background:
    radial-gradient(circle at 100% 0%, rgba(245, 158, 11, 0.12), transparent 34%),
    var(--color-surface);
}

.day-master-tag {
  border-color: rgba(245, 158, 11, 0.45) !important;
  color: #fbbf24 !important;
}

.bazi-intro {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-end;
  margin-bottom: 20px;
}

.bazi-kicker {
  display: block;
  color: #fbbf24;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  margin-bottom: 6px;
}

.bazi-intro p {
  margin: 0;
  max-width: 600px;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.favorable-elements {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-width: max-content;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.pillar-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin-bottom: 24px;
  background: rgba(245, 158, 11, 0.28);
  border: 1px solid rgba(245, 158, 11, 0.28);
  border-radius: 14px;
  overflow: hidden;
}

.pillar-item {
  display: flex;
  min-height: 136px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 18px 12px;
  background: linear-gradient(160deg, rgba(32, 27, 52, 0.96), rgba(20, 18, 34, 0.96));
}

.pillar-label {
  color: var(--color-text-muted);
  font-size: 13px;
}

.pillar-value {
  color: #fde68a;
  font-family: var(--font-family-display);
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-indent: 0.16em;
}

.pillar-ten-god {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.bazi-detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  gap: 20px;
}

.bazi-subsection {
  min-width: 0;
  padding: 18px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.12);
}

.subsection-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  color: var(--color-text);
  font-size: 15px;
  font-weight: 600;
}

.subsection-heading small {
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 400;
}

.element-list {
  display: flex;
  flex-direction: column;
  gap: 11px;
}

.element-row {
  display: grid;
  grid-template-columns: 20px 1fr 18px;
  align-items: center;
  gap: 10px;
}

.element-name,
.element-count {
  color: var(--color-text-secondary);
  font-size: 13px;
  text-align: center;
}

.element-track {
  height: 6px;
  overflow: hidden;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.08);
}

.element-fill {
  display: block;
  height: 100%;
  min-width: 3px;
  border-radius: inherit;
  transition: width 0.45s ease-out;
}

.element-木 { background: #34d399; }
.element-火 { background: #fb7185; }
.element-土 { background: #fbbf24; }
.element-金 { background: #cbd5e1; }
.element-水 { background: #38bdf8; }

.luck-cycle-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  max-height: 178px;
  overflow-y: auto;
  padding-right: 2px;
}

.luck-cycle {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 3px 8px;
  padding: 9px 10px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.035);
}

.luck-cycle strong {
  grid-row: span 2;
  color: var(--color-text);
  font-family: var(--font-family-display);
  font-size: 18px;
}

.luck-cycle-age,
.luck-cycle-year {
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.luck-cycle-year {
  color: var(--color-text-muted);
  font-size: 11px;
}

.luck-cycle.is-current {
  border-color: rgba(251, 191, 36, 0.55);
  background: rgba(245, 158, 11, 0.1);
}

.luck-cycle.is-current strong {
  color: #fde68a;
}

.bazi-notes {
  margin-top: 18px;
  padding: 12px 14px;
  border-left: 2px solid rgba(245, 158, 11, 0.65);
  background: rgba(245, 158, 11, 0.06);
}

.bazi-notes p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.65;
}

.bazi-notes p + p {
  margin-top: 4px;
}

.bazi-notes span {
  margin-right: 8px;
  color: var(--color-text-secondary);
  font-weight: 600;
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

.llm-source-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin: 0 0 20px 100px;
  padding: 15px 16px;
  border: 1px solid rgba(245, 158, 11, 0.28);
  border-radius: 12px;
  background: rgba(245, 158, 11, 0.06);
}

.llm-source-banner.is-server-default {
  border-color: rgba(99, 102, 241, 0.32);
  background: rgba(99, 102, 241, 0.08);
}

.llm-source-copy {
  min-width: 0;
}

.llm-source-kicker {
  display: block;
  margin-bottom: 4px;
  color: var(--color-primary-light);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.llm-source-copy strong {
  color: var(--color-text);
  font-size: 14px;
}

.llm-source-copy p {
  margin: 5px 0 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.55;
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

@media (max-width: 768px) {
  .llm-source-banner {
    align-items: flex-start;
    flex-direction: column;
    margin-left: 0;
  }

  .llm-row {
    flex-direction: column;
    gap: 0;
  }
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
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
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

  .bazi-intro {
    align-items: flex-start;
    flex-direction: column;
  }

  .favorable-elements {
    justify-content: flex-start;
  }

  .pillar-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pillar-item {
    min-height: 118px;
  }

  .bazi-detail-grid {
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

@media (prefers-reduced-motion: reduce) {
  .profile-page *,
  .profile-page *::before,
  .profile-page *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
