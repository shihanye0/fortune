import client from '@/shared/api/client'
import type { ApiResponse } from '@/shared/types/api'

export interface RegisterRequest {
  username: string
  email: string
  password: string
  birthDate?: string
  birthHour?: number
  gender?: string
  birthPlace?: string
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
