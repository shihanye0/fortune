<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const activeMenu = computed(() => route.name as string)

function handleMenuSelect(name: string) {
  router.push({ name })
}

async function handleLogout() {
  await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <div class="logo" @click="router.push('/')">
        <span class="logo-icon">🔮</span>
        <span class="logo-text">命理运势</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        :ellipsis="false"
        class="nav-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="home">首页</el-menu-item>
        <el-menu-item index="fortune">运势</el-menu-item>
        <el-menu-item index="divination">占卜</el-menu-item>
        <el-menu-item v-if="authStore.isLoggedIn" index="profile">个人</el-menu-item>
      </el-menu>
      <div class="header-actions">
        <template v-if="authStore.isLoggedIn">
          <span class="username">{{ authStore.user?.username }}</span>
          <el-button text @click="handleLogout">退出</el-button>
        </template>
        <template v-else>
          <el-button text @click="router.push('/login')">登录</el-button>
          <el-button type="primary" @click="router.push('/register')">注册</el-button>
        </template>
      </div>
    </el-header>
    <el-main class="app-main">
      <slot />
    </el-main>
  </el-container>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 0 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 18px;
  font-weight: bold;
  color: var(--color-primary);
}

.logo-icon {
  font-size: 24px;
}

.nav-menu {
  flex: 1;
  justify-content: center;
  border-bottom: none;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.app-main {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px;
  width: 100%;
}
</style>
