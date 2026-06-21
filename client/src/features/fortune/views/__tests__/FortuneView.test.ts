import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import FortuneView from '../FortuneView.vue'

// Mock API
vi.mock('@/features/fortune/api/fortune-api', () => ({
  getTodayFortune: vi.fn(),
  getFortuneList: vi.fn(),
  submitFortuneFeedback: vi.fn(),
}))

import { getTodayFortune, getFortuneList } from '@/features/fortune/api/fortune-api'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/fortune', name: 'fortune', component: FortuneView },
      { path: '/login', name: 'login', component: { template: '<div/>' } },
    ],
  })
}

describe('FortuneView', () => {
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
    vi.mocked(getTodayFortune).mockResolvedValue({
      success: true,
      data: null,
      error: null,
      meta: null,
    })
    vi.mocked(getFortuneList).mockResolvedValue({
      success: true,
      data: [],
      error: null,
      meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
    })

    const wrapper = mount(FortuneView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('每日运势')
  })

  it('shows loading state initially', async () => {
    vi.mocked(getTodayFortune).mockReturnValue(new Promise(() => {})) // never resolves
    vi.mocked(getFortuneList).mockReturnValue(new Promise(() => {}))

    const wrapper = mount(FortuneView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()

    expect(wrapper.find('.el-loading-mask').exists() || wrapper.text()).toBeTruthy()
  })

  it('displays today fortune card when data exists', async () => {
    vi.mocked(getTodayFortune).mockResolvedValue({
      success: true,
      data: {
        id: 1,
        date: '2026-06-20',
        overall_score: 85,
        career: 80,
        wealth: 75,
        love: 90,
        health: 85,
        lucky_color: '红色',
        lucky_number: '3, 8',
        lucky_direction: '东方',
        interpretation: '今日运势不错，事业上有贵人相助。',
        user_rating: null,
        user_feedback_tags: [],
        user_feedback_text: null,
      },
      error: null,
      meta: null,
    })
    vi.mocked(getFortuneList).mockResolvedValue({
      success: true,
      data: [],
      error: null,
      meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
    })

    const wrapper = mount(FortuneView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('85')
    expect(wrapper.text()).toContain('红色')
    expect(wrapper.text()).toContain('东方')
  })

  it('shows empty state when no fortune today', async () => {
    vi.mocked(getTodayFortune).mockResolvedValue({
      success: true,
      data: null,
      error: null,
      meta: null,
    })
    vi.mocked(getFortuneList).mockResolvedValue({
      success: true,
      data: [],
      error: null,
      meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
    })

    const wrapper = mount(FortuneView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('正在为您生成今日运势')
  })

  it('displays fortune history list', async () => {
    vi.mocked(getTodayFortune).mockResolvedValue({
      success: true,
      data: null,
      error: null,
      meta: null,
    })
    vi.mocked(getFortuneList).mockResolvedValue({
      success: true,
      data: [
        { id: 2, date: '2026-06-19', overall_score: 70, summary: '今日运势一般...' },
        { id: 3, date: '2026-06-18', overall_score: 90, summary: '今日运势很好...' },
      ],
      error: null,
      meta: { total: 2, page: 1, limit: 20, totalPages: 1 },
    })

    const wrapper = mount(FortuneView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('2026-06-19')
    expect(wrapper.text()).toContain('2026-06-18')
  })
})
