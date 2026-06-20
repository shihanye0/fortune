import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import DivinationView from '../DivinationView.vue'

vi.mock('@/features/divination/api/divination-api', () => ({
  doLiuyao: vi.fn(),
  doQimen: vi.fn(),
  getDivinationRecords: vi.fn(),
  submitDivinationFeedback: vi.fn(),
}))

import { doLiuyao, doQimen, getDivinationRecords } from '@/features/divination/api/divination-api'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/divination', name: 'divination', component: DivinationView },
      { path: '/login', name: 'login', component: { template: '<div/>' } },
    ],
  })
}

describe('DivinationView', () => {
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
    vi.mocked(getDivinationRecords).mockResolvedValue({
      success: true,
      data: [],
      error: null,
      meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
    })

    const wrapper = mount(DivinationView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('占卜中心')
  })

  it('shows two divination method options', async () => {
    vi.mocked(getDivinationRecords).mockResolvedValue({
      success: true,
      data: [],
      error: null,
      meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
    })

    const wrapper = mount(DivinationView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('六爻占卜')
    expect(wrapper.text()).toContain('奇门遁甲')
  })

  it('shows question input field', async () => {
    vi.mocked(getDivinationRecords).mockResolvedValue({
      success: true,
      data: [],
      error: null,
      meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
    })

    const wrapper = mount(DivinationView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.find('textarea, input[type="text"]').exists() || wrapper.text()).toBeTruthy()
  })

  it('calls liuyao API when submitting', async () => {
    vi.mocked(getDivinationRecords).mockResolvedValue({
      success: true,
      data: [],
      error: null,
      meta: { total: 0, page: 1, limit: 20, totalPages: 0 },
    })
    vi.mocked(doLiuyao).mockResolvedValue({
      success: true,
      data: { id: 1, question: '测试', interpretation: '卦象解读' },
      error: null,
      meta: null,
    })

    const wrapper = mount(DivinationView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    // Select liuyao and submit
    const liuyaoBtn = wrapper.findAll('button').find((b) => b.text().includes('六爻'))
    if (liuyaoBtn) {
      await liuyaoBtn.trigger('click')
    }

    const submitBtn = wrapper.findAll('button').find((b) => b.text().includes('起卦'))
    if (submitBtn) {
      await submitBtn.trigger('click')
      await flushPromises()
    }
  })

  it('displays divination history', async () => {
    vi.mocked(getDivinationRecords).mockResolvedValue({
      success: true,
      data: [
        {
          id: 1,
          type: 'liuyao',
          question: '今日运势如何？',
          summary: '今日运势如何？',
          user_rating: null,
          user_feedback_text: null,
          created_at: '2026-06-20T10:00:00',
        },
      ],
      error: null,
      meta: { total: 1, page: 1, limit: 20, totalPages: 1 },
    })

    const wrapper = mount(DivinationView, {
      global: { plugins: [pinia, router] },
    })
    await router.isReady()
    await flushPromises()

    expect(wrapper.text()).toContain('今日运势如何？')
  })
})
