import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import LoginView from '../LoginView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div/>' } },
      { path: '/login', name: 'login', component: LoginView },
      { path: '/register', name: 'register', component: { template: '<div/>' } },
    ],
  })
}

describe('LoginView', () => {
  let pinia: ReturnType<typeof createPinia>
  let router: ReturnType<typeof createTestRouter>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
  })

  it('renders login form', async () => {
    const wrapper = mount(LoginView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('登录')
    expect(wrapper.find('input').exists()).toBe(true)
  })

  it('has email and password inputs', async () => {
    const wrapper = mount(LoginView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    const inputs = wrapper.findAll('input')
    expect(inputs.length).toBeGreaterThanOrEqual(2)
  })

  it('has a login button', async () => {
    const wrapper = mount(LoginView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    const buttons = wrapper.findAll('button')
    const loginBtn = buttons.find((b) => b.text().includes('登录'))
    expect(loginBtn).toBeTruthy()
  })

  it('has a link to register page', async () => {
    const wrapper = mount(LoginView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('立即注册')
  })
})
