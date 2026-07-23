/** POST /safety/check (AI) */
import { aiClient } from '../client'
import { env } from '../env'
import type { SafetyCheckRequest, SafetyCheckResponse } from '@/types/dto'

export async function checkSafety(payload: SafetyCheckRequest): Promise<SafetyCheckResponse> {
  if (env.USE_MOCK) {
    const fn = async () => { const { mockGetSafetyAlerts } = await import('../mock'); const r = await mockGetSafetyAlerts(); return { caseId: payload.caseId, alerts: r.data } }
    return fn()
  }
  const { data } = await aiClient.post<SafetyCheckResponse>('/safety/check', payload)
  return data
}

/** AI 自动安全审核 — 独立方法 */
export async function autoSafetyCheck(caseId: string, symptoms: string[]): Promise<SafetyCheckResponse> {
  return checkSafety({ caseId, symptoms, triageResult: { riskLevel: '', urgency: '', department: '', recommendations: [], aiConfidence: 0 } })
}
