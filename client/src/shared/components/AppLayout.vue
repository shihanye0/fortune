<script setup lang="ts">
import { computed } from 'vue'
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
        <el-menu-item index="home">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="fortune">
          <el-icon><Sunny /></el-icon>
          <span>运势</span>
        </el-menu-item>
        <el-menu-item index="divination">
          <el-icon><MagicStick /></el-icon>
          <span>占卜</span>
        </el-menu-item>
        <el-menu-item v-if="authStore.isLoggedIn" index="profile">
          <el-icon><User /></el-icon>
          <span>个人</span>
        </el-menu-item>
      </el-menu>
      <div class="header-actions">
        <template v-if="authStore.isLoggedIn">
          <div class="user-info">
            <el-avatar :size="32" class="user-avatar">
              {{ authStore.user?.username?.charAt(0) || '用' }}
            </el-avatar>
            <span class="username">{{ authStore.user?.username }}</span>
          </div>
          <el-button text @click="handleLogout" class="logout-btn">退出</el-button>
        </template>
        <template v-else>
          <el-button text @click="router.push('/login')" class="login-btn">登录</el-button>
          <el-button type="primary" @click="router.push('/register')" class="register-btn">注册</el-button>
        </template>
      </div>
    </el-header>
    <el-main class="app-main">
      <slot />
    </el-main>
    <el-footer class="app-footer">
      <div class="footer-content">
        <span class="footer-logo">🔮 命理运势系统</span>
        <span class="footer-text">精准命理分析，每日运势推送</span>
      </div>
    </el-footer>
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
  background: rgba(22, 33, 62, 0.9);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  padding: 0 32px;
  height: 64px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.logo:hover {
  transform: scale(1.05);
}

.logo-icon {
  font-size: 28px;
  animation: float 3s ease-in-out infinite;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-family: var(--font-family-display);
}

.nav-menu {
  flex: 1;
  justify-content: center;
  border-bottom: none;
  background: transparent;
}

.nav-menu .el-menu-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  padding: 0 20px;
  height: 64px;
  line-height: 64px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: white;
  font-weight: bold;
}

.username {
  font-size: 14px;
  color: var(--color-text);
  font-weight: 500;
}

.logout-btn {
  color: var(--color-text-secondary) !important;
  transition: color 0.3s ease;
}

.logout-btn:hover {
  color: var(--color-accent) !important;
}

.login-btn {
  color: var(--color-text-secondary) !important;
  transition: color 0.3s ease;
}

.login-btn:hover {
  color: var(--color-accent) !important;
}

.register-btn {
  background: linear-gradient(135deg, var(--color-accent) 0%, #d97706 100%) !important;
  border: none !important;
  font-weight: 600;
  padding: 8px 20px;
}

.app-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
  width: 100%;
  min-height: calc(100vh - 64px - 80px);
}

.app-footer {
  background: rgba(22, 33, 62, 0.5);
  border-top: 1px solid var(--color-border);
  padding: 20px 32px;
  height: auto;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.footer-logo {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-accent);
}

.footer-text {
  font-size: 13px;
  color: var(--color-text-muted);
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* 响应式 */
@media (max-width: 768px) {
  .app-header {
    padding: 0 16px;
  }

  .logo-text {
    display: none;
  }

  .nav-menu .el-menu-item span {
    display: none;
  }

  .username {
    display: none;
  }

  .app-main {
    padding: 16px;
  }

  .footer-content {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>
