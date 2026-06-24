import client from '@/shared/api/client'
import type { ApiResponse } from '@/shared/types/api'

export interface LiuyaoRequest {
  question?: string
  method?: 'coin' | 'time'
}

export interface QimenRequest {
  question?: string
  mode: 'question' | 'realtime'
}

export interface DivinationResult {
  id: number
  question: string | null
  hexagram?: Record<string, unknown>
  chart?: Record<string, unknown>
  interpretation: string
}

export interface DivinationRecord {
  id: number
  type: 'liuyao' | 'qimen'
  question: string | null
  summary: string
  user_rating: number | null
  user_feedback_text: string | null
  accuracy_mark: number | null
  outcome_verified: boolean
  created_at: string
}

export interface ProbabilityEvent {
  dimension: string
  icon: string
  event: string
  description: string
  probability: number
  time_range: string
  best_hour: string
  element: string
  ten_god: string
  is_favorable: boolean
  feedback?: {
    occurred: boolean | null
    rating: number | null
    feedback_text: string | null
  }
}

export interface ProbabilityEventsData {
  date: string
  events: ProbabilityEvent[]
}

export interface EventFeedbackRequest {
  dimension: string
  event_name: string
  probability: number
  occurred?: boolean
  rating?: number
  feedback_text?: string
}

export async function doLiuyao(data: LiuyaoRequest): Promise<ApiResponse<DivinationResult>> {
  const res = await client.post('/api/v1/divination/liuyao', data)
  return res.data
}

export async function doQimen(data: QimenRequest): Promise<ApiResponse<DivinationResult>> {
  const res = await client.post('/api/v1/divination/qimen', data)
  return res.data
}

export async function getDivinationRecords(
  page = 1,
  limit = 20,
  type?: string
): Promise<ApiResponse<DivinationRecord[]>> {
  const res = await client.get('/api/v1/divination/records', { params: { page, limit, type } })
  return res.data
}

export async function getDivinationDetail(id: number): Promise<ApiResponse<DivinationResult>> {
  const res = await client.get(`/api/v1/divination/${id}`)
  return res.data
}

export async function submitDivinationFeedback(
  id: number,
  data: { rating: number; feedback_text?: string }
): Promise<ApiResponse<DivinationRecord>> {
  const res = await client.post(`/api/v1/divination/${id}/feedback`, data)
  return res.data
}

export async function getProbabilityEvents(): Promise<ApiResponse<ProbabilityEventsData>> {
  const res = await client.get('/api/v1/probability-events/today')
  return res.data
}

export async function submitEventFeedback(
  data: EventFeedbackRequest
): Promise<ApiResponse<{ message: string }>> {
  const res = await client.post('/api/v1/probability-events/feedback', data)
  return res.data
}
