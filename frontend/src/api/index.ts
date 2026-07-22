import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// Auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// === Patient APIs ===
export const patientApi = {
  list: (params?: any) => api.get('/patients', { params }),
  getById: (id: string) => api.get(`/patients/${id}`),
  create: (data: any) => api.post('/patients', data),
  update: (id: string, data: any) => api.put(`/patients/${id}`, data),
}

// === Triage APIs ===
export const triageApi = {
  getResult: (id: string) => api.get(`/triage/${id}`),
  submitForTriage: (data: any) => api.post('/triage', data),
  review: (id: string, data: any) => api.put(`/triage/${id}/review`, data),
}

// === AI / Safety APIs ===
export const aiApi = {
  getSafetyAlerts: () => api.get('/ai/safety-alerts'),
  getAgentStatus: (id: string) => api.get(`/ai/agent-run/${id}`),
  getGuidelines: (query: string) => api.get('/ai/guidelines', { params: { query } }),
}

// === Auth APIs ===
export const authApi = {
  login: (data: { email: string; password: string }) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  profile: () => api.get('/auth/profile'),
}

export default api
