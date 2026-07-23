/** POST /api/v1/auth/login */
import { apiClient } from '../client'
import { env } from '../env'
import type { LoginRequest, LoginResponse } from '@/types/dto'

export async function loginReal(payload: LoginRequest): Promise<LoginResponse> {
  if (env.USE_MOCK) {
    return { accessToken: 'MOCK_ACCESS_TOKEN_' + Date.now(), tokenType: 'Bearer', expiresIn: 3600, userId: 'mock-1', username: payload.username, roles: ['MEDICAL_STAFF'] }
  }
  const { data } = await apiClient.post<LoginResponse>('/auth/login', payload)
  return data
}

export async function getMe(): Promise<LoginResponse> {
  const { data } = await apiClient.get<LoginResponse>('/auth/me')
  return data
}
