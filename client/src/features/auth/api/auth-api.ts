import client from '@/shared/api/client'
import type { ApiResponse } from '@/shared/types/api'

export interface RegisterRequest {
  username: string
  email: string
  password: string
  birth_year: number
  birth_month: number
  birth_day: number
  birth_hour: number
  gender: number
  birth_location?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse {
  token: string
  user: {
    id: number
    username: string
    email: string
  }
}

export async function register(data: RegisterRequest): Promise<ApiResponse<AuthResponse>> {
  const res = await client.post('/api/v1/auth/register', data)
  return res.data
}

export async function login(data: LoginRequest): Promise<ApiResponse<AuthResponse>> {
  const res = await client.post('/api/v1/auth/login', data)
  return res.data
}
