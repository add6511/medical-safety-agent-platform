/**
 * POST /preconsultation/review (AI)
 * POST /pre-consultations/{id}/review (Spring Boot — 人工审核)
 */
import { aiClient, apiClient } from '../client'
import { env } from '../env'
import type { ReviewRequest, ReviewResponse } from '@/types/dto'

/** AI 辅助审核建议 — FastAPI */
export async function aiReview(payload: ReviewRequest): Promise<ReviewResponse> {
  if (env.USE_MOCK) {
    return { caseId: payload.caseId, status: 'ai_reviewed', reviewedAt: new Date().toISOString(), reviewedBy: 'MOCK-AI' }
  }
  const { data } = await aiClient.post<ReviewResponse>('/preconsultation/review', payload)
  return data
}

/** 人工审核提交 — Spring Boot（与 AI 审核分离） */
export async function submitManualReview(caseId: string, payload: { decision: string; doctorNote: string; department: string }): Promise<any> {
  if (env.USE_MOCK) {
    return { caseId, status: 'manual_reviewed', reviewedAt: new Date().toISOString(), reviewedBy: 'MOCK-医务人员' }
  }
  const { data } = await apiClient.post(`/pre-consultations/${caseId}/review`, payload)
  return data
}
