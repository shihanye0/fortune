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
  birth_minute: number | null
  gender: string | null
  birth_location: string | null
  push_channel: string | null
  push_enabled: boolean
  push_time: string | null
  feishu_webhook: string | null
  created_at: string
}

export async function getProfile(): Promise<ApiResponse<UserProfile>> {
  const res = await client.get('/api/v1/users/me')
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

export async function deleteAccount(password: string): Promise<ApiResponse<null>> {
  const res = await client.delete('/api/v1/users/me', { data: { password } })
  return res.data
}
