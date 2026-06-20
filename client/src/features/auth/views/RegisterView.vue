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
  birthDate: '',
  birthHour: null as number | null,
  gender: '',
  birthPlace: '',
})

async function handleRegister() {
  if (!form.username || !form.email || !form.password) {
    ElMessage.warning('请填写必填项')
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
      birthDate: form.birthDate || undefined,
      birthHour: form.birthHour ?? undefined,
      gender: form.gender || undefined,
      birthPlace: form.birthPlace || undefined,
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
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="form.password" type="password" placeholder="至少8位，含字母和数字" show-password />
        </el-form-item>
        <el-form-item label="确认密码" required>
          <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" show-password />
        </el-form-item>
        <el-divider>生辰信息（选填）</el-divider>
        <el-form-item label="出生日期">
          <el-date-picker v-model="form.birthDate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="出生时辰">
          <el-select v-model="form.birthHour" placeholder="选择时辰" style="width: 100%">
            <el-option v-for="h in 24" :key="h-1" :label="`${h-1}:00`" :value="h-1" />
          </el-select>
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio value="male">男</el-radio>
            <el-radio value="female">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出生地">
          <el-input v-model="form.birthPlace" placeholder="选填，用于真太阳时校正" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" style="width: 100%">
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
</style>
