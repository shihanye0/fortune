import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import AppLayout from '../AppLayout.vue'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
      { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
      { path: '/register', name: 'register', component: { template: '<div>Register</div>' } },
      { path: '/fortune', name: 'fortune', component: { template: '<div>Fortune</div>' } },
      { path: '/divination', name: 'divination', component: { template: '<div>Divination</div>' } },
      { path: '/profile', name: 'profile', component: { template: '<div>Profile</div>' } },
    ],
  })
}

describe('AppLayout', () => {
  let pinia: ReturnType<typeof createPinia>
  let router: ReturnType<typeof createTestRouter>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
  })

  it('renders logo with text', async () => {
    const wrapper = mount(AppLayout, {
      global: {
        plugins: [pinia, router],
      },
    })
    await router.isReady()

    expect(wrapper.find('.logo-text').text()).toBe('命理运势')
  })

  it('renders navigation menu items', async () => {
    const wrapper = mount(AppLayout, {
      global: {
        plugins: [pinia, router],
      },
    })
    await router.isReady()

    const menuItems = wrapper.findAll('.el-menu-item')
    const menuTexts = menuItems.map((item) => item.text())
    expect(menuTexts).toContain('首页')
    expect(menuTexts).toContain('运势')
    expect(menuTexts).toContain('占卜')
  })

  it('shows login and register buttons when not logged in', async () => {
    const wrapper = mount(AppLayout, {
      global: {
        plugins: [pinia, router],
      },
    })
    await router.isReady()

    expect(wrapper.text()).toContain('登录')
    expect(wrapper.text()).toContain('注册')
  })

  it('shows username and logout when logged in', async () => {
    // Set token in localStorage
    localStorage.setItem('token', 'test-token')

    const wrapper = mount(AppLayout, {
      global: {
        plugins: [pinia, router],
        stubs: {
          ElMessageBox: true,
        },
      },
    })
    await router.isReady()

    // Should show logout button
    expect(wrapper.text()).toContain('退出')

    // Cleanup
    localStorage.removeItem('token')
  })

  it('hides profile menu when not logged in', async () => {
    const wrapper = mount(AppLayout, {
      global: {
        plugins: [pinia, router],
      },
    })
    await router.isReady()

    const menuItems = wrapper.findAll('.el-menu-item')
    const menuTexts = menuItems.map((item) => item.text())
    expect(menuTexts).not.toContain('个人')
  })
})
