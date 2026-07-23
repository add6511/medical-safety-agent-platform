import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserRole } from '@/types/dto'

const ROLE_PERMS: Record<UserRole, string[]> = {
  patient: ['Dashboard', 'PreCheck'],
  doctor: ['Dashboard', 'ReviewList', 'Review', 'PreCheck'],
  followup: ['Dashboard', 'FollowUp'],
  admin: ['Dashboard', 'ReviewList', 'Review', 'PreCheck', 'AgentRuns', 'SafetyAudit', 'FollowUp'],
}

export const useAppStore = defineStore('app', () => {
  const user = ref<{ name: string; role: UserRole; token: string } | null>(null)
  const allowedRoutes = computed(() => user.value ? (ROLE_PERMS[user.value.role] || []) : [])
  function hasRoute(n: string) { return allowedRoutes.value.includes(n) }
  function login(name: string, role: UserRole, token: string) {
    user.value = { name, role, token }
    localStorage.setItem('accessToken', token)
    localStorage.setItem('user', JSON.stringify({ name, role }))
  }
  function logout() { user.value = null; localStorage.removeItem('accessToken'); localStorage.removeItem('user') }
  function loadUser() {
    const d = localStorage.getItem('user'); const t = localStorage.getItem('accessToken')
    if (d && t) { try { const { name, role } = JSON.parse(d); user.value = { name, role, token: t } } catch { /* ignore */ } }
  }
  return { user, allowedRoutes, hasRoute, login, logout, loadUser }
})
