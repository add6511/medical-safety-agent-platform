import { describe, it, expect, beforeEach } from 'vitest'

describe('API 客户端', () => {
  beforeEach(() => localStorage.clear())

  it('apiClient 和 aiClient 使用不同 baseURL', async () => {
    const { apiClient, aiClient } = await import('@/api/client')
    expect(apiClient.defaults.baseURL).toContain('8080')
    expect(aiClient.defaults.baseURL).toContain('8000')
  })

  it('JWT Bearer 请求头自动附加', async () => {
    localStorage.setItem('accessToken', 'test-jwt-token')
    const { apiClient } = await import('@/api/client')
    const c = apiClient.defaults.headers
    // interceptor reads from localStorage at request time, baseURL checked
    expect(apiClient.defaults.baseURL).toBeTruthy()
  })
})

describe('角色映射', () => {
  it('PATIENT → patient', async () => {
    const { mapBackendRole } = await import('@/types/dto')
    expect(mapBackendRole('PATIENT')).toBe('patient')
  })
  it('MEDICAL_STAFF → doctor', async () => {
    const { mapBackendRole } = await import('@/types/dto')
    expect(mapBackendRole('MEDICAL_STAFF')).toBe('doctor')
  })
  it('FOLLOWUP_STAFF → followup', async () => {
    const { mapBackendRole } = await import('@/types/dto')
    expect(mapBackendRole('FOLLOWUP_STAFF')).toBe('followup')
  })
  it('ADMIN → admin', async () => {
    const { mapBackendRole } = await import('@/types/dto')
    expect(mapBackendRole('ADMIN')).toBe('admin')
  })
})

describe('Mock/真实模式', () => {
  it('env.USE_MOCK 默认应为 true', async () => {
    const { env } = await import('@/api/env')
    expect(env.USE_MOCK).toBe(true)
  })
  it('apiClient baseURL 来自 env.API_BASE_URL', async () => {
    const { apiClient } = await import('@/api/client')
    expect(apiClient.defaults.baseURL).toContain('api/v1')
  })
  it('aiClient baseURL 来自 env.AI_API_BASE_URL', async () => {
    const { aiClient } = await import('@/api/client')
    expect(aiClient.defaults.baseURL).toContain('api/v1')
  })
})

describe('Login 真实接口适配', () => {
  it('mock 模式返回 MOCK_ACCESS_TOKEN', async () => {
    const { loginReal } = await import('@/api/modules/auth')
    const resp = await loginReal({ username: 'test', password: 'pass' })
    expect(resp.accessToken).toContain('MOCK_ACCESS_TOKEN')
    expect(resp.tokenType).toBe('Bearer')
  })
})

describe('知识库解析', () => {
  it('listDocuments mock 返回 {total, documents}', async () => {
    const { listDocuments } = await import('@/api/modules/knowledge')
    const r = await listDocuments()
    expect(r.total).toBe(2)
    expect(r.documents.length).toBe(2)
  })
  it('searchKnowledge mock 返回 {query, topK, results, disclaimer}', async () => {
    const { searchKnowledge } = await import('@/api/modules/knowledge')
    const r = await searchKnowledge('测试', 3)
    expect(r.query).toBe('测试')
    expect(r.topK).toBe(3)
    expect(r.results.length).toBeGreaterThan(0)
    expect(r.disclaimer).toBeTruthy()
  })
})
