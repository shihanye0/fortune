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
  deleteAccount,
} from '../api/profile-api'
import type { UserProfile } from '../api/profile-api'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(true)
const profile = ref<UserProfile | null>(null)

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
  llm_api_key: '',
  llm_api_url: '',
  llm_model: '',
})

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
    return lunar.getYearShengXiao()
  } catch {
    return '未知'
  }
}

// 星座
function getConstellation(month: number, day: number): string {
  const dates = [20, 19, 21, 20, 21, 22, 23, 23, 23, 24, 22, 22]
  const signs = ['水瓶座', '双鱼座', '白羊座', '金牛座', '双子座', '巨蟹座', '狮子座', '处女座', '天秤座', '天蝎座', '射手座', '摩羯座']
  return day < dates[month - 1] ? signs[month - 1] : signs[month % 12]
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
      llmForm.llm_provider = res.data.llm_provider || ''
      llmForm.llm_api_key = res.data.llm_api_key || ''
      llmForm.llm_api_url = res.data.llm_api_url || ''
      llmForm.llm_model = res.data.llm_model || ''
    }
  } catch {
    ElMessage.error('加载个人信息失败')
  } finally {
    loading.value = false
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
      <el-card class="section-card animate-fade-in">
        <template #header>
          <div class="card-title">
            <span class="card-icon">🤖</span>
            <span>LLM 配置</span>
          </div>
        </template>
        <el-form label-width="100px" class="llm-form">
          <el-form-item label="供应商名称">
            <el-input v-model="llmForm.llm_provider" placeholder="例如：DeepSeek、Xiaomi MiMo" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="llmForm.llm_api_key" type="password" placeholder="输入 API Key" show-password />
          </el-form-item>
          <el-form-item label="API URL">
            <el-input v-model="llmForm.llm_api_url" placeholder="例如：https://api.deepseek.com/v1" />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="llmForm.llm_model" placeholder="例如：deepseek-chat" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleUpdateLLMSettings">保存 LLM 配置</el-button>
          </el-form-item>
        </el-form>
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

/* 危险操作 */
.danger-card {
  border-color: rgba(239, 68, 68, 0.3) !important;
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
}
</style>
