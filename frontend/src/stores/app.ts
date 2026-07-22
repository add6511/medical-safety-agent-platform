import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface PatientCase {
  id: string
  name: string
  gender: string
  age: number
  symptoms: string[]
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'pending' | 'reviewing' | 'approved' | 'completed'
  createdAt: string
  triageResult?: TriageResult
  followUpPlan?: FollowUpPlan
  safetyAlerts?: SafetyAlert[]
}

export interface TriageResult {
  riskLevel: string
  urgency: string
  department: string
  recommendations: string[]
  aiConfidence: number
}

export interface FollowUpPlan {
  id: string
  tasks: FollowUpTask[]
  schedule: string
  compliance: number
}

export interface FollowUpTask {
  id: string
  title: string
  dueDate: string
  completed: boolean
  type: 'medication' | 'checkup' | 'lifestyle' | 'consultation'
}

export interface SafetyAlert {
  id: string
  level: 'warning' | 'danger' | 'info'
  message: string
  source: string
  timestamp: string
}

export const useAppStore = defineStore('app', () => {
  const user = ref<{ name: string; role: string; token: string } | null>(null)
  const patients = ref<PatientCase[]>([])
  const currentPatient = ref<PatientCase | null>(null)

  function login(name: string, role: string, token: string) {
    user.value = { name, role, token }
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify({ name, role }))
  }

  function logout() {
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function loadUser() {
    const data = localStorage.getItem('user')
    const token = localStorage.getItem('token')
    if (data && token) {
      const { name, role } = JSON.parse(data)
      user.value = { name, role, token }
    }
  }

  return { user, patients, currentPatient, login, logout, loadUser }
})
