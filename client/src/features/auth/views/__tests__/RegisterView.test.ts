import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import RegisterView from '../RegisterView.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div/>' } },
      { path: '/login', name: 'login', component: { template: '<div/>' } },
      { path: '/register', name: 'register', component: RegisterView },
    ],
  })
}

describe('RegisterView', () => {
  let pinia: ReturnType<typeof createPinia>
  let router: ReturnType<typeof createTestRouter>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
  })

  it('renders register form', async () => {
    const wrapper = mount(RegisterView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('注册')
  })

  it('has required form fields', async () => {
    const wrapper = mount(RegisterView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('用户名')
    expect(wrapper.text()).toContain('邮箱')
    expect(wrapper.text()).toContain('密码')
    expect(wrapper.text()).toContain('确认密码')
  })

  it('has birth info section', async () => {
    const wrapper = mount(RegisterView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('生辰信息')
    expect(wrapper.text()).toContain('出生日期')
    expect(wrapper.text()).toContain('出生时辰')
  })

  it('has a register button', async () => {
    const wrapper = mount(RegisterView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    const buttons = wrapper.findAll('button')
    const registerBtn = buttons.find((b) => b.text().includes('注册'))
    expect(registerBtn).toBeTruthy()
  })

  it('has a link to login page', async () => {
    const wrapper = mount(RegisterView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('立即登录')
  })
})
