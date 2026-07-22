/**
 * Mock API 数据层 — 后端接口未就绪时的演示数据
 * 与后端接口格式完全对齐，替换 baseURL 即可切换真实接口
 */
import type { PatientCase, TriageResult, FollowUpPlan, SafetyAlert } from '@/stores/app'

// 模拟网络延迟
const delay = (ms = 400) => new Promise(r => setTimeout(r, ms))

// ==================== Auth ====================
export async function mockLogin(email: string, _password: string) {
  await delay(600)
  const roleMap: Record<string, { name: string; role: string; token: string }> = {
    'doctor@hospital.com': { name: '李医生', role: 'doctor', token: 'mock-token-doctor-' + Date.now() },
    'admin@hospital.com': { name: '管理员', role: 'admin', token: 'mock-token-admin-' + Date.now() },
    'patient@demo.com': { name: '模拟患者', role: 'patient', token: 'mock-token-patient-' + Date.now() },
  }
  const user = roleMap[email]
  if (!user) throw new Error('邮箱或密码错误')
  return { success: true, data: user }
}

// ==================== Patients ====================
const mockPatients: PatientCase[] = [
  { id: 'P20240301', name: '张三', gender: '男', age: 45, symptoms: ['胸痛', '呼吸困难', '心悸'], severity: 'critical', status: 'pending', createdAt: '2024-03-15 09:30' },
  { id: 'P20240302', name: '李四', gender: '女', age: 32, symptoms: ['头痛', '眩晕', '恶心'], severity: 'high', status: 'reviewing', createdAt: '2024-03-15 10:15' },
  { id: 'P20240303', name: '王五', gender: '男', age: 28, symptoms: ['发热', '咳嗽', '乏力'], severity: 'medium', status: 'approved', createdAt: '2024-03-15 11:00' },
  { id: 'P20240304', name: '赵六', gender: '女', age: 55, symptoms: ['关节痛', '晨僵'], severity: 'low', status: 'completed', createdAt: '2024-03-15 08:45' },
  { id: 'P20240305', name: '孙七', gender: '男', age: 67, symptoms: ['意识模糊', '血压升高', '言语不清'], severity: 'critical', status: 'pending', createdAt: '2024-03-15 13:20' },
  { id: 'P20240306', name: '周八', gender: '女', age: 41, symptoms: ['腹痛', '腹泻', '脱水'], severity: 'high', status: 'reviewing', createdAt: '2024-03-15 14:00' },
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

// ==================== Triage ====================
export async function mockTriage(data: any) {
  await delay(1000)
  const hasHeartSymptoms = data.symptoms?.some((s: string) => ['胸痛', '呼吸困难', '心悸', '意识模糊'].includes(s))
  const result: TriageResult = {
    riskLevel: hasHeartSymptoms ? '危急' : data.symptoms?.length > 3 ? '高风险' : '中风险',
    urgency: hasHeartSymptoms ? '紧急' : '需关注',
    department: hasHeartSymptoms ? '心血管内科 / 急诊科' : '内科',
    recommendations: hasHeartSymptoms
      ? ['立即进行 ECG 和肌钙蛋白检测', '心血管内科紧急会诊', '监测生命体征']
      : ['常规检查', '观察症状变化', '随访评估'],
    aiConfidence: 0.85 + Math.random() * 0.12,
  }
  return { data: result }
}

// ==================== Follow-ups ====================
export async function mockGetFollowUps() {
  await delay()
  return {
    data: {
      tasks: [
        { id: '1', title: '复查心电图 + 肌钙蛋白', dueDate: '2024-03-22', completed: true, type: 'checkup' },
        { id: '2', title: '按时服用阿司匹林 100mg/天', dueDate: '2024-04-15', completed: false, type: 'medication' },
        { id: '3', title: '低盐低脂饮食，每日步行30分钟', dueDate: '2024-04-01', completed: false, type: 'lifestyle' },
        { id: '4', title: '心血管内科复诊', dueDate: '2024-03-30', completed: false, type: 'consultation' },
        { id: '5', title: '血压监测每周2次并记录', dueDate: '2024-03-20', completed: false, type: 'checkup' },
      ],
      compliance: 20,
    },
  }
}

// ==================== AI / Safety ====================
const mockAlerts: SafetyAlert[] = [
  { id: '1', level: 'danger', message: 'P20240301 症状匹配心肌梗死模式，请立即审核！', source: 'AI 安全 Agent', timestamp: '09:32' },
  { id: '2', level: 'warning', message: 'P20240305 NIHSS 评分 >15，疑似脑卒中', source: 'AI 安全 Agent', timestamp: '13:22' },
  { id: '3', level: 'info', message: 'P20240303 症状组合低风险，建议常规处理', source: 'AI 预检 Agent', timestamp: '11:05' },
]

export async function mockGetSafetyAlerts() {
  await delay()
  return { data: mockAlerts }
}

export async function mockGetAgentRuns() {
  await delay()
  return {
    data: [
      { id: 'RUN-001', caseId: 'P20240301', type: '安全预检 Agent', status: '完成', duration: '1.2s', tokens: 1847, startedAt: '2024-03-15 09:30:15' },
      { id: 'RUN-002', caseId: 'P20240305', type: '安全检查 Agent', status: '完成', duration: '0.8s', tokens: 1256, startedAt: '2024-03-15 13:20:08' },
      { id: 'RUN-003', caseId: 'P20240302', type: '安全预检 Agent', status: '运行中', duration: '0.5s', tokens: 623, startedAt: '2024-03-15 14:30:00' },
    ],
  }
}
