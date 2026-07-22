import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
    {
      path: '/',
      component: () => import('@/components/Layout.vue'),
      redirect: '/dashboard',
      children: [
        { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/MedicalDashboard.vue'), meta: { requiresAuth: true } },
        { path: 'pre-check', name: 'PreCheck', component: () => import('@/views/PatientPreCheck.vue'), meta: { requiresAuth: true } },
        { path: 'review-list', name: 'ReviewList', component: () => import('@/views/ReviewList.vue'), meta: { requiresAuth: true } },
        { path: 'review/:id', name: 'Review', component: () => import('@/views/ReviewConsole.vue'), meta: { requiresAuth: true } },
        { path: 'follow-up', name: 'FollowUp', component: () => import('@/views/FollowUpPlan.vue'), meta: { requiresAuth: true } },
        { path: 'agent-runs', name: 'AgentRuns', component: () => import('@/views/AgentRuns.vue'), meta: { requiresAuth: true } },
        { path: 'safety-audit', name: 'SafetyAudit', component: () => import('@/views/SafetyAudit.vue'), meta: { requiresAuth: true } },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) next('/login')
    else next()
  } else { next() }
})

export default router
