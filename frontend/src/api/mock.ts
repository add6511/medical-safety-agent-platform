/**
 * Mock API 数据层 — 合成教学案例
 * 所有案例均为虚构，仅用于教学演示
 * 格式与后端接口对齐，切换 baseURL 即可对接真实接口
 */
import type { PatientCase, TriageResult, SafetyAlert } from '@/stores/app'

const delay = (ms = 400) => new Promise(r => setTimeout(r, ms))

// ==================== Auth ====================
export async function mockLogin(email: string, _password: string) {
  await delay(600)
  const roleMap: Record<string, { name: string; role: string; token: string }> = {
    'doctor@hospital.com': { name: '教学-医务人员', role: 'doctor', token: 'MOCK_TOKEN_DOCTOR_' + Date.now() },
    'admin@hospital.com': { name: '教学-管理员', role: 'admin', token: 'MOCK_TOKEN_ADMIN_' + Date.now() },
    'patient@demo.com': { name: '教学-模拟患者', role: 'patient', token: 'MOCK_TOKEN_PATIENT_' + Date.now() },
  }
  const user = roleMap[email]
  if (!user) throw new Error('邮箱或密码错误')
  return { success: true, data: user }
}

// ==================== Patients (合成教学案例) ====================
const mockPatients: PatientCase[] = [
  { id: 'SYN-20240301', name: '合成案例001', gender: '男', age: 45, symptoms: ['红旗症状A', '红旗症状B', '红旗症状C'], severity: 'critical', status: 'pending', createdAt: '2024-03-15 09:30' },
  { id: 'SYN-20240302', name: '合成案例002', gender: '女', age: 32, symptoms: ['模拟症状D', '模拟症状E', '模拟症状F'], severity: 'high', status: 'reviewing', createdAt: '2024-03-15 10:15' },
  { id: 'SYN-20240303', name: '合成案例003', gender: '男', age: 28, symptoms: ['模拟症状G', '模拟症状H', '模拟症状I'], severity: 'medium', status: 'approved', createdAt: '2024-03-15 11:00' },
  { id: 'SYN-20240304', name: '合成案例004', gender: '女', age: 55, symptoms: ['模拟症状J', '模拟症状K'], severity: 'low', status: 'completed', createdAt: '2024-03-15 08:45' },
  { id: 'SYN-20240305', name: '合成案例005', gender: '男', age: 67, symptoms: ['红旗症状L', '红旗症状M', '红旗症状N'], severity: 'critical', status: 'pending', createdAt: '2024-03-15 13:20' },
  { id: 'SYN-20240306', name: '合成案例006', gender: '女', age: 41, symptoms: ['模拟症状O', '模拟症状P', '模拟症状Q'], severity: 'high', status: 'reviewing', createdAt: '2024-03-15 14:00' },
]

export async function mockGetPatients() {
  await delay()
  return { data: mockPatients, total: mockPatients.length }
}

export async function mockGetPatient(id: string) {
  await delay()
  const p = mockPatients.find(x => x.id === id)
  if (!p) throw new Error('案例不存在')
  return { data: p }
}

// ==================== Triage (中性风险提示) ====================
export async function mockTriage(data: any) {
  await delay(1000)
  const flagCount = data.symptoms?.filter((s: string) => s.startsWith('红旗')).length || 0
  const result: TriageResult = {
    riskLevel: flagCount >= 3 ? '需紧急人工审核' : flagCount >= 1 ? '需重点关注' : '低风险（合成数据）',
    urgency: flagCount >= 3 ? '紧急' : '常规',
    department: '待医务人员确定',
    recommendations: flagCount >= 3
      ? ['检测到多个红旗症状组合，请医务人员立即人工审核', '建议综合评估后确定处置方案', '本结果为AI辅助提示，不能替代专业判断']
      : ['AI已完成初步筛查', '请医务人员根据实际情况判断', '本结果为AI辅助提示，不能替代专业判断'],
    aiConfidence: 0.85 + Math.random() * 0.12,
  }
  return { data: result }
}

// ==================== AI / Safety Alerts ====================
const mockAlerts: SafetyAlert[] = [
  { id: '1', level: 'danger', message: 'SYN-20240301 检测到多个红旗症状组合，请立即人工审核！', source: 'AI 辅助筛查', timestamp: '09:32' },
  { id: '2', level: 'warning', message: 'SYN-20240305 检测到需要重点关注的风险指标', source: 'AI 辅助筛查', timestamp: '13:22' },
  { id: '3', level: 'info', message: 'SYN-20240303 常规风险水平，建议按标准流程处理', source: 'AI 辅助筛查', timestamp: '11:05' },
]

export async function mockGetSafetyAlerts() {
  await delay()
  return { data: mockAlerts }
}

export async function mockGetAgentRuns() {
  await delay()
  return {
    data: [
      { id: 'RUN-001', caseId: 'SYN-20240301', type: '辅助筛查 Agent', status: '完成', duration: '1.2s', tokens: 1847, startedAt: '2024-03-15 09:30:15' },
      { id: 'RUN-002', caseId: 'SYN-20240305', type: '辅助筛查 Agent', status: '完成', duration: '0.8s', tokens: 1256, startedAt: '2024-03-15 13:20:08' },
      { id: 'RUN-003', caseId: 'SYN-20240302', type: '辅助筛查 Agent', status: '运行中', duration: '0.5s', tokens: 623, startedAt: '2024-03-15 14:30:00' },
    ],
  }
}
