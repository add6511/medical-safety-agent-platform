/**
 * DTO 类型 — 与后端 Spring Boot + FastAPI AI 服务对齐
 * snake_case 接口返回 → 适配层转换为 camelCase
 */
export type UserRole = 'patient' | 'doctor' | 'followup' | 'admin'

// ===== Login =====
export interface LoginRequest { username: string; password: string }
export interface LoginResponse {
  accessToken: string; tokenType: string; expiresIn: number
  userId: string; username: string; roles: string[]
}
/** 后端角色 → 前端角色映射 */
export function mapBackendRole(r: string): UserRole {
  const m: Record<string, UserRole> = { PATIENT: 'patient', MEDICAL_STAFF: 'doctor', FOLLOWUP_STAFF: 'followup', ADMIN: 'admin' }
  return m[r] || 'patient'
}

// ===== Patient =====
export interface PatientCase {
  id: string; name: string; gender: string; age: number
  symptoms: string[]; severity: string; status: string; createdAt: string
  triageResult?: TriageResult; safetyAlerts?: SafetyAlert[]
}
export interface TriageResult { riskLevel: string; urgency: string; department: string; recommendations: string[]; aiConfidence: number }
export interface SafetyAlert { id: string; level: 'warning'|'danger'|'info'; message: string; source: string; timestamp: string }

// ===== AI 服务 DTO =====
export interface TriageRequest { patientId: string; symptoms: string[]; duration: string; severity: number }
export interface TriageAnalyzeResponse { caseId: string; result: TriageResult; agentRunId: string }
export interface SafetyCheckRequest { caseId: string; symptoms: string[]; triageResult: TriageResult }
export interface SafetyCheckResponse { caseId: string; alerts: SafetyAlert[] }
export interface ReviewRequest { caseId: string; decision: string; doctorNote: string; department: string }
export interface ReviewResponse { caseId: string; status: string; reviewedAt: string; reviewedBy: string }

// 知识库
export interface KnowledgeDocument { id: string; title: string; content: string; source: string; createdAt: string; tags: string[] }
export interface KnowledgeListResponse { total: number; documents: KnowledgeDocument[] }
export interface KnowledgeSearchResponse { query: string; topK: number; results: { document: KnowledgeDocument; score: number; highlights: string[] }[]; disclaimer: string }

// ===== 后端 Spring Boot DTO =====
export interface TriageResultBackend {
  id: string; patientCaseId: string; riskLevel: string; urgency: string
  department: string; recommendations: string[]; aiConfidence: number; createdAt: string
}
export interface AgentLogRequest { triageResultId: string; agentType: string; input: any }
