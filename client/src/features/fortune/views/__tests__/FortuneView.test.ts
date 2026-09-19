import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import FortuneView from '../FortuneView.vue'

// Mock API
vi.mock('@/features/fortune/api/fortune-api', () => ({
  getTodayFortune: vi.fn(),
  getFortuneList: vi.fn(),
  getWeeklyForecast: vi.fn(),
  submitFortuneFeedback: vi.fn(),
}))

import { getTodayFortune, getFortuneList, getWeeklyForecast } from '@/features/fortune/api/fortune-api'

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
    vi.mocked(getWeeklyForecast).mockResolvedValue({
      success: true,
      data: [],
      error: null,
      meta: null,
    })
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
        overall_score: 5,
        career: { score: 4, description: '工作节奏顺畅' },
        wealth: { score: 3, description: '预算优先' },
        love: { score: 5, description: '沟通自然' },
        health: { score: 4, description: '留意作息' },
        lucky_color: '红色',
        lucky_number: '3, 8',
        lucky_direction: '东方',
        hourly_fortunes: null,
        interpretation: '今日运势不错，事业上有贵人相助。',
        user_rating: null,
        user_feedback_tags: [],
        user_feedback_text: null,
        accuracy_mark: null,
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

    expect(wrapper.text()).toContain('5')
    expect(wrapper.text()).toContain('顺势')
    expect(wrapper.text()).toContain('今日行动简报')
    expect(wrapper.text()).toContain('优先安排')
    expect(wrapper.text()).toContain('留出余地')
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

  it('keeps today fortune available when optional weekly forecast fails', async () => {
    vi.mocked(getTodayFortune).mockResolvedValue({
      success: true,
      data: {
        id: 1, date: '2026-06-20', overall_score: 4,
        career: { score: 4, description: '工作节奏顺畅' },
        wealth: { score: 3, description: '预算优先' },
        love: { score: 4, description: '沟通自然' },
        health: { score: 3, description: '留意作息' },
        lucky_color: '红色', lucky_number: '3, 8', lucky_direction: '东方', hourly_fortunes: null,
        interpretation: '今天适合稳步推进。', user_rating: null, user_feedback_tags: [],
        user_feedback_text: null, accuracy_mark: null,
      },
      error: null,
      meta: null,
    })
    vi.mocked(getFortuneList).mockResolvedValue({
      success: true, data: [], error: null,
      meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
    })
    vi.mocked(getWeeklyForecast).mockRejectedValue(new Error('week endpoint unavailable'))

    const wrapper = mount(FortuneView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('今日行动简报')
    expect(wrapper.text()).not.toContain('七日节奏')
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
        { id: 2, date: '2026-06-19', overall_score: 2, summary: '今日运势一般...' },
        { id: 3, date: '2026-06-18', overall_score: 5, summary: '今日运势很好...' },
      ],
      error: null,
      meta: { total: 2, page: 1, limit: 20, totalPages: 1 },
    })

    const wrapper = mount(FortuneView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    // 检查日期是否显示（新格式显示为 19 和 06月）
    expect(wrapper.text()).toContain('19')
    expect(wrapper.text()).toContain('18')
    expect(wrapper.text()).toContain('06月')
  })

  it('renders the seven-day forecast and switches the selected day', async () => {
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
    vi.mocked(getWeeklyForecast).mockResolvedValue({
      success: true,
      data: [
        {
          date: '2026-09-18', weekday: '周五', heavenly_stem: '甲', earthly_branch: '子',
          overall_score: 3, overall_level: '平',
          focus: { key: 'career', label: '事业', score: 3, detail: '先完成核心事项。' }, caution: null,
        },
        {
          date: '2026-09-19', weekday: '周六', heavenly_stem: '乙', earthly_branch: '丑',
          overall_score: 4, overall_level: '偏吉',
          focus: { key: 'love', label: '关系', score: 4, detail: '适合主动沟通。' },
          caution: { key: 'wealth', label: '财务', score: 2, detail: '避免冲动消费。' },
        },
      ],
      error: null,
      meta: null,
    })

    const wrapper = mount(FortuneView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('七日节奏')
    expect(wrapper.text()).toContain('本周最佳 · 周六')
    await wrapper.findAll('.week-forecast-day')[1].trigger('click')
    expect(wrapper.text()).toContain('优先安排 关系')
    expect(wrapper.text()).toContain('避免冲动消费')
  })
})
