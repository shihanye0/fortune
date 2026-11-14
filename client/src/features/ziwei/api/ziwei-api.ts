import client from '@/shared/api/client'
import type { ApiResponse } from '@/shared/types/api'

const LLM_INTERPRETATION_TIMEOUT = 120000

export interface ZiweiStar {
  name: string
  brightness: string | null
  mutagen: string | null
}

export interface ZiweiPalace {
  name: string
  branch: string
  stem: string
  major_stars: ZiweiStar[]
  minor_stars: ZiweiStar[]
  da_xian: { start: number; end: number }
  is_soul: boolean
  is_body: boolean
}

export interface ZiweiChart {
  birth: { solar: string; shichen_name: string; shichen_range: string; gender: string }
  lunar: { year_ganzhi: string; month: number; day: number; is_leap: boolean; zodiac: string }
  soul_palace: string
  body_palace: string
  five_elements: string
  ju: number
  ming_zhu: string
  shen_zhu: string
  current_age: number
  palaces: ZiweiPalace[]
  da_xians: { start_age: number; end_age: number; palace_name: string; branch: string }[]
  flow_year: { year: number; ganzhi: string; ming_gong_branch: string; sihua_stars: string[] }
  notes: string[]
}

export interface DivinationRecord {
  id: number
  type: 'liuyao' | 'qimen' | 'ziwei'
  question: string | null
  summary: string
  user_rating: number | null
  accuracy_mark: number | null
  created_at: string
}

export async function doZiwei(data: { question?: string }): Promise<ApiResponse<ZiweiChart & { id: number; interpretation: string }>> {
  const res = await client.post('/api/v1/divination/ziwei', data, { timeout: LLM_INTERPRETATION_TIMEOUT })
  return res.data
}

export async function getZiweiRecords(page = 1, limit = 20): Promise<ApiResponse<DivinationRecord[]>> {
  const res = await client.get('/api/v1/divination/records', { params: { page, limit, type: 'ziwei' } })
  return res.data
}

export async function submitDivinationFeedback(id: number, data: { rating: number; feedback_text?: string }): Promise<ApiResponse<DivinationRecord>> {
  const res = await client.post(`/api/v1/divination/${id}/feedback`, data)
  return res.data
}

export async function getZiweiChart(): Promise<ApiResponse<ZiweiChart>> {
  const res = await client.get('/api/v1/users/me/ziwei-chart')
  return res.data
}
