import client from '@/shared/api/client'
import type { ApiResponse, PaginationMeta } from '@/shared/types/api'

export interface FortuneDimension {
  score: number
  description: string
}

export interface FortuneDetail {
  id: number
  date: string
  overall_score: number
  career: FortuneDimension
  wealth: FortuneDimension
  love: FortuneDimension
  health: FortuneDimension
  lucky_color: string
  lucky_number: string
  lucky_direction: string
  interpretation: string
  user_rating: number | null
  user_feedback_tags: string[]
  user_feedback_text: string | null
}

export interface FortuneListItem {
  id: number
  date: string
  overall_score: number
  summary: string
}

export interface FortuneFeedback {
  rating: number
  tags?: string[]
  feedback_text?: string
}

export async function getTodayFortune(): Promise<ApiResponse<FortuneDetail | null>> {
  const res = await client.get('/api/v1/fortunes/today')
  return res.data
}

export async function getFortuneList(page = 1, limit = 20): Promise<ApiResponse<FortuneListItem[]>> {
  const res = await client.get('/api/v1/fortunes', { params: { page, limit } })
  return res.data
}

export async function getFortuneDetail(id: number): Promise<ApiResponse<FortuneDetail>> {
  const res = await client.get(`/api/v1/fortunes/${id}`)
  return res.data
}

export async function submitFortuneFeedback(
  id: number,
  data: FortuneFeedback
): Promise<ApiResponse<FortuneDetail>> {
  const res = await client.post(`/api/v1/fortunes/${id}/feedback`, data)
  return res.data
}
