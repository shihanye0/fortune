import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '../types/user'
import { login as loginApi, register as registerApi } from '../api/auth-api'
import type { LoginRequest, RegisterRequest } from '../api/auth-api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isLoggedIn = computed(() => !!token.value)

  async function login(data: LoginRequest) {
    const res = await loginApi(data)
    if (res.success && res.data) {
      token.value = res.data.token
      localStorage.setItem('token', res.data.token)
      user.value = res.data.user as User
    }
    return res
  }

  async function register(data: RegisterRequest) {
    const res = await registerApi(data)
    if (res.success && res.data) {
      token.value = res.data.token
      localStorage.setItem('token', res.data.token)
      user.value = res.data.user as User
    }
    return res
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  return { user, token, isLoggedIn, login, register, logout }
})
