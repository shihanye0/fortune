import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'

vi.mock('@/features/ziwei/api/ziwei-api', () => ({
  getZiweiChart: vi.fn(),
  doZiwei: vi.fn(),
  getZiweiRecords: vi.fn(),
  submitDivinationFeedback: vi.fn(),
}))
vi.mock('@/features/feedback/api/feedback-api', () => ({
  submitDivinationAccuracy: vi.fn(),
  submitPredictionOutcome: vi.fn(),
}))

import ZiweiView from '../ZiweiView.vue'
import {
  getZiweiChart, doZiwei, getZiweiRecords,
} from '@/features/ziwei/api/ziwei-api'
import type { ZiweiChart } from '@/features/ziwei/api/ziwei-api'

const mockChart = {
  birth: { solar: '1990-8-15', shichen_name: '辰时', shichen_range: '07:00-09:00', gender: '女' },
  lunar: { year_ganzhi: '庚午', month: 6, day: 25, is_leap: false, zodiac: '马' },
  soul_palace: '卯', body_palace: '亥', five_elements: '土五局', ju: 5,
  ming_zhu: '文曲', shen_zhu: '火星', current_age: 37,
  palaces: Array.from({ length: 12 }, (_, i) => ({
    name: i === 0 ? '命宫' : ['父母', '福德', '田宅', '官禄', '仆役', '迁移', '疾厄', '财帛', '子女', '夫妻', '兄弟'][i - 1],
    branch: ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑'][i],
    stem: '甲', major_stars: [], minor_stars: [],
    da_xian: { start: 5, end: 14 }, is_soul: i === 0, is_body: false,
  })),
  da_xians: [], flow_year: { year: 2026, ganzhi: '丙午', ming_gong_branch: '午', sihua_stars: ['天同', '天机', '文昌', '廉贞'] },
  notes: ['排盘口径：农历正月初一换年（主流紫微口径，与八字立春口径不同）'],
}

const mountView = async () => {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', name: 'home', component: { template: '<div/>' } }] })
  localStorage.setItem('token', 'test-token')
  const wrapper = mount(ZiweiView, { global: { plugins: [pinia, router] } })
  await flushPromises()
  return wrapper
}

describe('ZiweiView', () => {
  beforeEach(() => {
    vi.mocked(getZiweiChart).mockResolvedValue({ success: true, data: mockChart, error: null, meta: null })
    vi.mocked(getZiweiRecords).mockResolvedValue({ success: true, data: [], error: null, meta: null })
    vi.mocked(doZiwei).mockResolvedValue({ success: true, data: { ...mockChart, id: 1, interpretation: '命宫主星文曲，善于表达。' }, error: null, meta: null })
  })

  it('加载命盘并渲染十二宫', async () => {
    const wrapper = await mountView()
    expect(getZiweiChart).toHaveBeenCalled()
    expect(wrapper.text()).toContain('命盘十二宫')
    expect(wrapper.text()).toContain('土五局')
  })

  it('生成解读后展示文本与历史刷新', async () => {
    const wrapper = await mountView()
    await wrapper.findAll('button').find(b => b.text().includes('生成 AI 解读'))!.trigger('click')
    await flushPromises()
    expect(doZiwei).toHaveBeenCalled()
    expect(wrapper.text()).toContain('命宫主星文曲')
    expect(vi.mocked(getZiweiRecords).mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('无生辰时显示错误提示与重试', async () => {
    vi.mocked(getZiweiChart).mockResolvedValue({ success: false, data: null as unknown as ZiweiChart, error: { message: '生辰信息不完整', code: 'BIRTH_INCOMPLETE' }, meta: null })
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('命盘暂不可用')
  })

})
