<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const features = [
  {
    icon: '📊',
    title: '每日运势',
    desc: '基于八字排盘，精准推算每日事业、财运、感情、健康四维运势。',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  {
    icon: '🎯',
    title: '六爻占卜',
    desc: '传统铜钱法起卦，AI 智能解读卦象，为你指点迷津。',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  },
  {
    icon: '🌌',
    title: '奇门遁甲',
    desc: '时家奇门排盘，九星八门八神一目了然，洞察天时地利。',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  },
]
</script>

<template>
  <div class="home-page">
    <!-- Hero 区域 -->
    <section class="hero animate-fade-in">
      <div class="hero-content">
        <div class="hero-badge">🔮 传统命理 × AI 解读</div>
        <h1 class="hero-title">
          <span class="title-main">命理运势系统</span>
          <span class="title-sub">每日精准运势，尽在掌握</span>
        </h1>
        <p class="hero-desc">
          融合传统八字命理与现代 AI 技术，为您提供精准的每日运势分析、
          六爻占卜、奇门遁甲排盘等专业命理服务。
        </p>
        <div class="hero-actions">
          <el-button
            v-if="!authStore.isLoggedIn"
            type="primary"
            size="large"
            @click="router.push('/register')"
            class="cta-button"
          >
            立即注册，开启运势之旅
          </el-button>
          <el-button
            v-else
            type="primary"
            size="large"
            @click="router.push('/fortune')"
            class="cta-button"
          >
            查看今日运势
          </el-button>
          <el-button
            size="large"
            @click="router.push('/divination')"
            class="secondary-button"
          >
            开始占卜
          </el-button>
        </div>
        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-number">143+</span>
            <span class="stat-label">单元测试</span>
          </div>
          <div class="stat-item">
            <span class="stat-number">33+</span>
            <span class="stat-label">前端测试</span>
          </div>
          <div class="stat-item">
            <span class="stat-number">24+</span>
            <span class="stat-label">E2E测试</span>
          </div>
        </div>
      </div>
      <div class="hero-visual">
        <div class="fortune-circle">
          <div class="circle-inner">
            <span class="circle-icon">☯</span>
            <span class="circle-text">天人合一</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能卡片 -->
    <section class="features-section">
      <h2 class="section-title">核心功能</h2>
      <div class="features-grid">
        <el-card
          v-for="(feature, index) in features"
          :key="index"
          class="feature-card"
          shadow="hover"
          @click="router.push(index === 0 ? '/fortune' : '/divination')"
        >
          <div class="feature-icon" :style="{ background: feature.gradient }">
            {{ feature.icon }}
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-desc">{{ feature.desc }}</p>
          <div class="feature-arrow">→</div>
        </el-card>
      </div>
    </section>

  </div>
</template>

<style scoped>
.home-page {
  padding: 0;
}

/* Hero 区域 */
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 80px 0 60px;
  gap: 60px;
}

.hero-content {
  flex: 1;
  max-width: 600px;
}

.hero-badge {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 20px;
  font-size: 14px;
  color: var(--color-primary-light);
  margin-bottom: 24px;
}

.hero-title {
  margin-bottom: 24px;
}

.title-main {
  display: block;
  font-size: 48px;
  font-weight: 800;
  font-family: var(--font-family-display);
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.title-sub {
  display: block;
  font-size: 20px;
  color: var(--color-accent);
  margin-top: 12px;
  font-weight: 500;
}

.hero-desc {
  font-size: 16px;
  color: var(--color-text-secondary);
  line-height: 1.8;
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 48px;
}

.cta-button {
  padding: 14px 32px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  border-radius: 12px !important;
}

.secondary-button {
  padding: 14px 32px !important;
  font-size: 16px !important;
  border-radius: 12px !important;
  border: 2px solid var(--color-border) !important;
  color: var(--color-text) !important;
  background: transparent !important;
  transition: all 0.3s ease;
}

.secondary-button:hover {
  border-color: var(--color-primary) !important;
  color: var(--color-primary) !important;
}

.hero-stats {
  display: flex;
  gap: 40px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 32px;
  font-weight: 800;
  color: var(--color-accent);
  font-family: var(--font-family-display);
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.hero-visual {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.fortune-circle {
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(245, 158, 11, 0.2) 100%);
  border: 2px solid rgba(99, 102, 241, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  animation: float 6s ease-in-out infinite;
  position: relative;
}

.fortune-circle::before {
  content: '';
  position: absolute;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  border: 1px solid rgba(99, 102, 241, 0.1);
  animation: pulse 3s infinite;
}

.circle-inner {
  text-align: center;
}

.circle-icon {
  font-size: 80px;
  display: block;
  margin-bottom: 16px;
  animation: spin 20s linear infinite;
}

.circle-text {
  font-size: 18px;
  color: var(--color-accent);
  font-family: var(--font-family-display);
  letter-spacing: 8px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.05); opacity: 0.8; }
}

/* 功能卡片 */
.features-section {
  padding: 80px 0;
}

.section-title {
  font-size: 32px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 48px;
  font-family: var(--font-family-display);
  color: var(--color-text);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-card {
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 32px;
  text-align: center;
}

.feature-card:hover {
  transform: translateY(-8px);
}

.feature-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  margin: 0 auto 24px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}

.feature-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text);
}

.feature-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 20px;
}

.feature-arrow {
  font-size: 20px;
  color: var(--color-primary);
  transition: transform 0.3s ease;
}

.feature-card:hover .feature-arrow {
  transform: translateX(8px);
}


/* 响应式 */
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    padding: 40px 0;
    gap: 40px;
  }

  .title-main {
    font-size: 32px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .hero-stats {
    justify-content: center;
  }

  .fortune-circle {
    width: 200px;
    height: 200px;
  }

  .circle-icon {
    font-size: 60px;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .tech-grid {
    grid-template-columns: 1fr;
  }
}
</style>
