import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import HomeView from '../HomeView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: HomeView },
      { path: '/login', name: 'login', component: { template: '<div/>' } },
      { path: '/register', name: 'register', component: { template: '<div/>' } },
      { path: '/fortune', name: 'fortune', component: { template: '<div/>' } },
      { path: '/divination', name: 'divination', component: { template: '<div/>' } },
    ],
  })
}

describe('HomeView', () => {
  let pinia: ReturnType<typeof createPinia>
  let router: ReturnType<typeof createTestRouter>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
  })

  it('renders hero title', async () => {
    const wrapper = mount(HomeView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.find('.hero-title').text()).toContain('命理运势系统')
  })

  it('renders hero subtitle', async () => {
    const wrapper = mount(HomeView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('每日精准运势，尽在掌握')
  })

  it('shows register button when not logged in', async () => {
    const wrapper = mount(HomeView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('立即注册')
  })

  it('shows fortune button when logged in', async () => {
    localStorage.setItem('token', 'test-token')
    const wrapper = mount(HomeView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('查看今日运势')
    localStorage.removeItem('token')
  })

  it('renders three feature cards', async () => {
    const wrapper = mount(HomeView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('每日运势')
    expect(wrapper.text()).toContain('六爻占卜')
    expect(wrapper.text()).toContain('奇门遁甲')
  })
})
