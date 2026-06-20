<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
</script>

<template>
  <div class="home-page">
    <section class="hero">
      <h1 class="hero-title">🔮 命理运势系统</h1>
      <p class="hero-subtitle">每日精准运势，尽在掌握</p>
      <div class="hero-actions">
        <el-button
          v-if="!authStore.isLoggedIn"
          type="primary"
          size="large"
          @click="router.push('/register')"
        >
          立即注册
        </el-button>
        <el-button
          v-else
          type="primary"
          size="large"
          @click="router.push('/fortune')"
        >
          查看今日运势
        </el-button>
        <el-button size="large" @click="router.push('/divination')">
          开始占卜
        </el-button>
      </div>
    </section>

    <section class="features">
      <el-row :gutter="24">
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>📊 每日运势</template>
            <p>基于八字排盘，精准推算每日事业、财运、感情、健康四维运势。</p>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>🎯 六爻占卜</template>
            <p>传统铜钱法起卦，AI 智能解读卦象，为你指点迷津。</p>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>🌌 奇门遁甲</template>
            <p>时家奇门排盘，九星八门八神一目了然，洞察天时地利。</p>
          </el-card>
        </el-col>
      </el-row>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  padding: 40px 0;
}

.hero {
  text-align: center;
  padding: 60px 0;
}

.hero-title {
  font-size: 48px;
  margin-bottom: 16px;
}

.hero-subtitle {
  font-size: 20px;
  color: var(--color-text-secondary);
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.features {
  margin-top: 40px;
}
</style>
