/** POST /triage/analyze (AI) + Spring Boot triage-results */
import { aiClient, apiClient } from '../client'
import { env } from '../env'
import type { TriageRequest, TriageAnalyzeResponse, TriageResultBackend, AgentLogRequest } from '@/types/dto'

export async function analyzeTriage(payload: TriageRequest): Promise<TriageAnalyzeResponse> {
  if (env.USE_MOCK) {
    const fn = async () => { const { mockTriage } = await import('../mock'); return mockTriage(payload) }
    return fn()
  }
  const { data } = await aiClient.post<TriageAnalyzeResponse>('/triage/analyze', payload)
  return data
}

/** GET /triage-results/pre-consultation/{id} — Spring Boot */
export async function getTriageResult(id: string): Promise<TriageResultBackend> {
  const { data } = await apiClient.get<TriageResultBackend>(`/triage-results/pre-consultation/${id}`)
  return data
}

/** POST /triage-results — Spring Boot */
export async function createTriageResult(payload: any): Promise<TriageResultBackend> {
  const { data } = await apiClient.post<TriageResultBackend>('/triage-results', payload)
  return data
}

/** POST /triage-results/agent-logs — Spring Boot */
export async function createAgentLog(payload: AgentLogRequest): Promise<any> {
  const { data } = await apiClient.post('/triage-results/agent-logs', payload)
  return data
}
