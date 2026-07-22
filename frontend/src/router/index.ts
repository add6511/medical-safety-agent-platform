import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/MedicalDashboard.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/pre-check',
      name: 'PreCheck',
      component: () => import('@/views/PatientPreCheck.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/review/:id',
      name: 'Review',
      component: () => import('@/views/ReviewConsole.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/follow-up',
      name: 'FollowUp',
      component: () => import('@/views/FollowUpPlan.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

// Simple auth guard
router.beforeEach((to, _from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) {
      next('/login')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
