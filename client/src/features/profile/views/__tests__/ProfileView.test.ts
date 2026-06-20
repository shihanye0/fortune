import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ProfileView from '../ProfileView.vue'

vi.mock('@/features/profile/api/profile-api', () => ({
  getProfile: vi.fn(),
  updateProfile: vi.fn(),
  updateBirth: vi.fn(),
  updatePushSettings: vi.fn(),
  deleteAccount: vi.fn(),
}))

import { getProfile } from '@/features/profile/api/profile-api'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/profile', name: 'profile', component: ProfileView },
      { path: '/login', name: 'login', component: { template: '<div/>' } },
    ],
  })
}

const mockProfile = {
  id: 1,
  username: '测试用户',
  email: 'test@example.com',
  birth_year: 1990,
  birth_month: 5,
  birth_day: 15,
  birth_hour: 8,
  gender: 'male',
  birth_location: '北京',
  push_channel: 'email',
  push_enabled: true,
  push_time: '07:00',
  feishu_webhook: null,
  created_at: '2026-06-20T00:00:00',
}

describe('ProfileView', () => {
  let pinia: ReturnType<typeof createPinia>
  let router: ReturnType<typeof createTestRouter>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
    vi.clearAllMocks()
    localStorage.setItem('token', 'test-token')
  })

  afterEach(() => {
    localStorage.removeItem('token')
  })

  it('renders page title', async () => {
    vi.mocked(getProfile).mockResolvedValue({
      success: true,
      data: mockProfile,
      error: null,
      meta: null,
    })

    const wrapper = mount(ProfileView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('个人中心')
  })

  it('displays user info', async () => {
    vi.mocked(getProfile).mockResolvedValue({
      success: true,
      data: mockProfile,
      error: null,
      meta: null,
    })

    const wrapper = mount(ProfileView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('测试用户')
    expect(wrapper.text()).toContain('test@example.com')
  })

  it('displays birth info section', async () => {
    vi.mocked(getProfile).mockResolvedValue({
      success: true,
      data: mockProfile,
      error: null,
      meta: null,
    })

    const wrapper = mount(ProfileView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('生辰信息')
    expect(wrapper.text()).toContain('1990')
  })

  it('displays push settings section', async () => {
    vi.mocked(getProfile).mockResolvedValue({
      success: true,
      data: mockProfile,
      error: null,
      meta: null,
    })

    const wrapper = mount(ProfileView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('推送设置')
  })
})
