<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'
import {
  getProfile,
  updateProfile,
  updateBirth,
  updatePushSettings,
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
})

const pushForm = reactive({
  push_enabled: false,
  push_channel: 'email',
  push_time: '07:00',
  feishu_webhook: '',
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
      pushForm.push_enabled = res.data.push_enabled
      pushForm.push_channel = res.data.push_channel || 'email'
      pushForm.push_time = res.data.push_time || '07:00'
      pushForm.feishu_webhook = res.data.feishu_webhook || ''
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
    <h1 class="page-title">个人中心</h1>

    <template v-if="profile">
      <!-- 基本信息 -->
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-button text @click="editingUsername = !editingUsername">
              {{ editingUsername ? '取消' : '编辑' }}
            </el-button>
          </div>
        </template>
        <div v-if="!editingUsername">
          <p>用户名：{{ profile.username }}</p>
          <p>邮箱：{{ profile.email }}</p>
        </div>
        <div v-else>
          <el-input v-model="usernameForm.username" placeholder="新用户名" />
          <el-button type="primary" @click="handleUpdateUsername" style="margin-top: 12px">
            保存
          </el-button>
        </div>
      </el-card>

      <!-- 生辰信息 -->
      <el-card class="section-card">
        <template #header>
          <div class="card-header">
            <span>生辰信息</span>
            <el-button text @click="editingBirth = !editingBirth">
              {{ editingBirth ? '取消' : '修改生辰' }}
            </el-button>
          </div>
        </template>
        <div v-if="!editingBirth">
          <p>
            出生：{{ profile.birth_year }}-{{ String(profile.birth_month).padStart(2, '0') }}-{{ String(profile.birth_day).padStart(2, '0') }}
            {{ profile.birth_hour }}:00
          </p>
        </div>
        <div v-else>
          <el-form label-width="80px">
            <el-form-item label="年">
              <el-input-number v-model="birthForm.birth_year" :min="1900" :max="2100" />
            </el-form-item>
            <el-form-item label="月">
              <el-input-number v-model="birthForm.birth_month" :min="1" :max="12" />
            </el-form-item>
            <el-form-item label="日">
              <el-input-number v-model="birthForm.birth_day" :min="1" :max="31" />
            </el-form-item>
            <el-form-item label="时辰">
              <el-select v-model="birthForm.birth_hour">
                <el-option v-for="h in 24" :key="h-1" :label="`${h-1}:00`" :value="h-1" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleUpdateBirth">保存</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>

      <!-- 推送设置 -->
      <el-card class="section-card">
        <template #header>推送设置</template>
        <el-form label-width="100px">
          <el-form-item label="每日推送">
            <el-switch v-model="pushForm.push_enabled" />
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

      <!-- 危险操作 -->
      <el-card class="section-card danger-card">
        <template #header>危险操作</template>
        <el-button type="danger" @click="handleDeleteAccount">注销账号</el-button>
      </el-card>
    </template>
  </div>
</template>

<style scoped>
.profile-page {
  padding: 20px 0;
}

.page-title {
  margin-bottom: 24px;
}

.section-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.danger-card {
  border-color: #f56c6c;
}
</style>
