import client from '@/shared/api/client'
import type { ApiResponse } from '@/shared/types/api'

export interface UserProfile {
  id: number
  username: string
  email: string
  birth_year: number | null
  birth_month: number | null
  birth_day: number | null
  birth_hour: number | null
  gender: number | null
  birth_location: string | null
  push_channel: string | null
  push_enabled: boolean
  push_time: string | null
  feishu_webhook: string | null
  llm_provider: string | null
  llm_notes: string | null
  llm_website: string | null
  llm_api_key: string | null
  llm_api_key_url: string | null
  llm_api_url: string | null
  llm_model: string | null
  llm_config_source: 'personal' | 'server_default'
  created_at: string
}

export interface BaziPillar {
  key: 'year' | 'month' | 'day' | 'hour'
  label: string
  pillar: string
  ten_god: string | null
}

export interface MajorLuckCycle {
  start_age: number
  end_age: number
  start_year: number
  end_year: number
  pillar: string
}

export interface BaziProfile {
  pillars: BaziPillar[]
  day_master: string
  five_elements: Record<string, number>
  favorable_elements: string[]
  major_luck_cycles: MajorLuckCycle[]
  calculation_note: string
  usage_notice: string
}

export async function getProfile(): Promise<ApiResponse<UserProfile>> {
  const res = await client.get('/api/v1/users/me')
  return res.data
}

export async function getBaziProfile(): Promise<ApiResponse<BaziProfile>> {
  const res = await client.get('/api/v1/users/me/bazi-profile')
  return res.data
}

export async function updateProfile(username: string): Promise<ApiResponse<UserProfile>> {
  const res = await client.put('/api/v1/users/me', { username })
  return res.data
}

export async function updateBirth(data: {
  birth_year: number
  birth_month: number
  birth_day: number
  birth_hour: number
  gender?: number
  birth_location?: string | null
}): Promise<ApiResponse<UserProfile>> {
  const res = await client.put('/api/v1/users/me/birth', data)
  return res.data
}

export async function updatePushSettings(data: {
  push_enabled: boolean
  push_channel: string
  push_time: string
  feishu_webhook?: string
}): Promise<ApiResponse<UserProfile>> {
  const res = await client.put('/api/v1/users/me/push-settings', data)
  return res.data
}

export async function updateLLMSettings(data: {
  llm_provider?: string
  llm_notes?: string
  llm_website?: string
  llm_api_key?: string
  llm_api_key_url?: string
  llm_api_url?: string
  llm_model?: string
  use_server_default?: boolean
}): Promise<ApiResponse<UserProfile>> {
  const res = await client.put('/api/v1/users/me/llm-settings', data)
  return res.data
}

export async function testLLMConnection(data?: {
  llm_api_key?: string
  llm_api_url?: string
  llm_model?: string
}): Promise<ApiResponse<{ status: string; message: string; model: string; provider: string }>> {
  const res = await client.post('/api/v1/users/me/llm-test', data || {})
  return res.data
}

export async function deleteAccount(password: string): Promise<ApiResponse<null>> {
  const res = await client.delete('/api/v1/users/me', { data: { password } })
  return res.data
}
