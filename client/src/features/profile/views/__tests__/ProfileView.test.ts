import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import ProfileView from '../ProfileView.vue'

vi.mock('@/features/profile/api/profile-api', () => ({
  getProfile: vi.fn(),
  getBaziProfile: vi.fn(),
  updateProfile: vi.fn(),
  updateBirth: vi.fn(),
  updatePushSettings: vi.fn(),
  updateLLMSettings: vi.fn(),
  deleteAccount: vi.fn(),
}))

vi.mock('@/features/feedback/api/feedback-api', () => ({
  getAccuracyStats: vi.fn(),
  submitFortuneAccuracy: vi.fn(),
  submitDivinationAccuracy: vi.fn(),
  submitPredictionOutcome: vi.fn(),
}))

import { getBaziProfile, getProfile } from '@/features/profile/api/profile-api'
import { getAccuracyStats } from '@/features/feedback/api/feedback-api'

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
  gender: 1,
  birth_location: '北京',
  push_channel: 'email',
  push_enabled: true,
  push_time: '07:00',
  feishu_webhook: null,
  llm_provider: null,
  llm_notes: null,
  llm_website: null,
  llm_api_key: null,
  llm_api_key_url: null,
  llm_api_url: null,
  llm_model: null,
  llm_config_source: 'server_default' as const,
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
    vi.mocked(getAccuracyStats).mockResolvedValue({
      success: true,
      data: {
        fortune_accuracy: { total: 10, accurate: 7, rate: 70 },
        divination_accuracy: { total: 5, accurate: 4, rate: 80 },
        dimension_accuracy: {
          career: { total: 10, accurate: 8, rate: 80 },
          wealth: { total: 10, accurate: 6, rate: 60 },
        },
      },
      error: null,
      meta: null,
    })
    vi.mocked(getBaziProfile).mockResolvedValue({
      success: true,
      data: {
        pillars: [
          { key: 'year', label: '年柱', pillar: '庚午', ten_god: '比肩' },
          { key: 'month', label: '月柱', pillar: '辛巳', ten_god: '劫财' },
          { key: 'day', label: '日柱', pillar: '庚辰', ten_god: '日主' },
          { key: 'hour', label: '时柱', pillar: '庚辰', ten_god: '比肩' },
        ],
        day_master: '庚',
        five_elements: { 金: 4, 木: 0, 水: 0, 火: 2, 土: 2 },
        favorable_elements: ['水', '木'],
        major_luck_cycles: [
          { start_age: 8, end_age: 17, start_year: 1997, end_year: 2006, pillar: '壬午' },
        ],
        calculation_note: '四柱按节气计算',
        usage_notice: '仅供传统文化参考',
      },
      error: null,
      meta: null,
    })
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

  it('displays transparent bazi chart data', async () => {
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

    expect(wrapper.text()).toContain('命盘基础')
    expect(wrapper.text()).toContain('庚午')
    expect(wrapper.text()).toContain('四柱按节气计算')
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
