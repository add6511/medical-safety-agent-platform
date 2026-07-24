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
  safetyAlerts?: SafetyAlert[]
}

export interface TriageResult {
  riskLevel: string
  urgency: string
  department: string
  recommendations: string[]
  aiConfidence: number
}

export interface SafetyAlert {
  id: string
  level: 'warning' | 'danger' | 'info'
  message: string
  source: string
  timestamp: string
}

export interface AppUser {
  userId: number
  name: string
  role: string
  token: string
}

export const useAppStore = defineStore('app', () => {
  const user = ref<AppUser | null>(null)
  const patients = ref<PatientCase[]>([])
  const currentPatient = ref<PatientCase | null>(null)

  function login(
    userId: number,
    name: string,
    role: string,
    token: string,
  ) {
    user.value = {
      userId,
      name,
      role,
      token,
    }

    localStorage.setItem('token', token)
    localStorage.setItem(
      'user',
      JSON.stringify({
        userId,
        name,
        role,
      }),
    )
  }

  function logout() {
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function loadUser() {
    const data = localStorage.getItem('user')
    const token = localStorage.getItem('token')

    if (!data || !token) {
      return
    }

    try {
      const parsed = JSON.parse(data) as {
        userId?: number
        name?: string
        role?: string
      }

      if (
        typeof parsed.userId !== 'number' ||
        !parsed.name ||
        !parsed.role
      ) {
        logout()
        return
      }

      user.value = {
        userId: parsed.userId,
        name: parsed.name,
        role: parsed.role,
        token,
      }
    } catch {
      logout()
    }
  }

  return {
    user,
    patients,
    currentPatient,
    login,
    logout,
    loadUser,
  }
})