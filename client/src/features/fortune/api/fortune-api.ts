import client from '@/shared/api/client'
import type { ApiResponse } from '@/shared/types/api'

export interface FortuneDimension {
  score: number
  description?: string
  detail?: string
}

export interface HourlyFortune {
  shichen: string
  shichen_range: string
  hourly_stem: string
  hourly_branch: string
  score: number
  ten_god: string
  element: string
  atmosphere: string
  energy: string
  events: string[]
  favorable: string[]
  unfavorable: string[]
}

export interface FortuneDetail {
  id: number
  date: string
  overall_score: number
  overall_level?: string
  career: FortuneDimension
  wealth: FortuneDimension
  love: FortuneDimension
  health: FortuneDimension
  lucky_color: string
  lucky_number: string
  lucky_direction: string
  hourly_fortunes: HourlyFortune[] | null
  interpretation: string
  user_rating: number | null
  user_feedback_tags: string[]
  user_feedback_text: string | null
  accuracy_mark: number | null
}

export interface FortuneListItem {
  id: number
  date: string
  overall_score: number
  overall_level?: string
  summary: string
}

export interface FortuneFeedback {
  rating: number
  tags?: string[]
  feedback_text?: string
}

export interface WeeklyFortuneFocus {
  key: 'career' | 'wealth' | 'love' | 'health'
  label: string
  score: number
  detail: string
}

export interface WeeklyFortuneItem {
  date: string
  weekday: string
  heavenly_stem: string
  earthly_branch: string
  overall_score: number
  overall_level: string
  focus: WeeklyFortuneFocus
  caution: WeeklyFortuneFocus | null
}

export async function getTodayFortune(): Promise<ApiResponse<FortuneDetail | null>> {
  const res = await client.get('/api/v1/fortunes/today')
  return res.data
}

export async function regenerateTodayFortune(): Promise<ApiResponse<FortuneDetail>> {
  const res = await client.post('/api/v1/fortunes/today/regenerate', null, { timeout: 60000 })
  return res.data
}

export async function getFortuneList(page = 1, limit = 20): Promise<ApiResponse<FortuneListItem[]>> {
  const res = await client.get('/api/v1/fortunes', { params: { page, limit } })
  return res.data
}

export async function getWeeklyForecast(): Promise<ApiResponse<WeeklyFortuneItem[]>> {
  const res = await client.get('/api/v1/fortunes/week')
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
