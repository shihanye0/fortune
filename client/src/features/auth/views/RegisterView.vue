<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  birthYear: null as number | null,
  birthMonth: null as number | null,
  birthDay: null as number | null,
  birthHour: null as number | null,
  gender: null as number | null,
  birthLocation: '',
})

async function handleRegister() {
  if (!form.username || !form.email || !form.password) {
    ElMessage.warning('请填写必填项')
    return
  }
  if (
    form.birthYear === null || form.birthMonth === null || form.birthDay === null
    || form.birthHour === null || form.gender === null
  ) {
    ElMessage.warning('请完整填写生辰信息后再注册')
    return
  }
  if (form.password !== form.confirmPassword) {
    ElMessage.error('两次密码不一致')
    return
  }
  if (form.password.length < 8) {
    ElMessage.error('密码至少8位')
    return
  }
  loading.value = true
  try {
    const res = await authStore.register({
      username: form.username,
      email: form.email,
      password: form.password,
      birth_year: form.birthYear,
      birth_month: form.birthMonth,
      birth_day: form.birthDay,
      birth_hour: form.birthHour,
      gender: form.gender,
      birth_location: form.birthLocation || undefined,
    })
    if (res.success) {
      ElMessage.success('注册成功')
      router.push('/')
    } else {
      ElMessage.error(res.error?.message || '注册失败')
    }
  } catch {
    ElMessage.error('网络错误，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <el-card class="register-card">
      <template #header>
        <h2>注册</h2>
      </template>
      <p class="register-intro">生辰信息用于生成命盘基础；请按阳历和出生时刻如实填写。</p>
      <el-form :model="form" label-width="80px" @submit.prevent="handleRegister">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" name="username" autocomplete="username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" name="email" type="email" autocomplete="email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="form.password" name="new-password" type="password" autocomplete="new-password" placeholder="至少8位，含字母和数字" show-password />
        </el-form-item>
        <el-form-item label="确认密码" required>
          <el-input v-model="form.confirmPassword" name="confirm-password" type="password" autocomplete="new-password" placeholder="再次输入密码" show-password />
        </el-form-item>
        <el-divider>生辰信息（用于排盘）</el-divider>
        <el-form-item label="出生年" required>
          <el-input-number v-model="form.birthYear" :min="1900" :max="2100" placeholder="年" style="width: 100%" />
        </el-form-item>
        <el-form-item label="出生月" required>
          <el-input-number v-model="form.birthMonth" :min="1" :max="12" placeholder="月" style="width: 100%" />
        </el-form-item>
        <el-form-item label="出生日" required>
          <el-input-number v-model="form.birthDay" :min="1" :max="31" placeholder="日" style="width: 100%" />
        </el-form-item>
        <el-form-item label="出生时辰" required>
          <el-select v-model="form.birthHour" placeholder="选择时辰" style="width: 100%">
            <el-option v-for="h in 24" :key="h-1" :label="`${h-1}:00`" :value="h-1" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别" required>
          <el-radio-group v-model="form.gender">
            <el-radio :value="1">男</el-radio>
            <el-radio :value="0">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出生地">
          <el-input v-model="form.birthLocation" name="birth-location" autocomplete="address-level2" placeholder="选填；当前不会用于真太阳时校正" />
        </el-form-item>
        <el-form-item>
          <el-button native-type="submit" type="primary" :loading="loading" style="width: 100%">
            注册
          </el-button>
        </el-form-item>
        <el-form-item>
          <span>已有账号？<router-link to="/login">立即登录</router-link></span>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  padding-top: 40px;
}

.register-card {
  width: 520px;
}

.register-intro {
  margin: 0 0 20px;
  padding: 10px 12px;
  border-left: 3px solid var(--color-accent);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: rgba(245, 158, 11, 0.08);
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.7;
}
</style>
