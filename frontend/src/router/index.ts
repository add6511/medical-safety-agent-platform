import { createRouter, createWebHistory } from 'vue-router'
import type { UserRole } from '@/types/dto'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
    { path: '/403', name: 'Forbidden', component: () => import('@/views/Forbidden.vue') },
    { path: '/', component: () => import('@/components/Layout.vue'), redirect: '/dashboard', children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/MedicalDashboard.vue'), meta: { roles: ['patient','doctor','followup','admin'] } },
      { path: 'pre-check', name: 'PreCheck', component: () => import('@/views/PatientPreCheck.vue'), meta: { roles: ['patient','doctor','admin'] } },
      { path: 'review-list', name: 'ReviewList', component: () => import('@/views/ReviewList.vue'), meta: { roles: ['doctor','admin'] } },
      { path: 'review/:id', name: 'Review', component: () => import('@/views/ReviewConsole.vue'), meta: { roles: ['doctor','admin'] } },
      { path: 'agent-runs', name: 'AgentRuns', component: () => import('@/views/AgentRuns.vue'), meta: { roles: ['admin'] } },
      { path: 'safety-audit', name: 'SafetyAudit', component: () => import('@/views/SafetyAudit.vue'), meta: { roles: ['admin'] } },
    ]},
  ],
})

router.beforeEach((to, _from, next) => {
  const roles = to.meta.roles as string[] | undefined
  if (!roles) return next()
  const token = localStorage.getItem('accessToken')
  if (!token) return next('/login')
  try {
    const raw = localStorage.getItem('user')
    if (!raw) return next('/login')
    const { role } = JSON.parse(raw) as { role: UserRole }
    if (!roles.includes(role)) return next('/403')
    next()
  } catch { next('/login') }
})
export default router
