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

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  tokenType: string
  expiresIn: number
  userId: number
  username: string
  roles: string[]
}

export interface CurrentUserResponse {
  userId: number
  username: string
  displayName: string
  caseCode: string | null
  status: string
  roles: string[]
}

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>('/v1/auth/login', data),

  me: () =>
    api.get<CurrentUserResponse>('/v1/auth/me'),
}
// === Medical Record APIs ===

export interface CreateMedicalRecordRequest {
  patientId: number
  caseCode: string
  chiefComplaint?: string
  presentIllness?: string
  pastHistory?: string
  allergyHistory?: string
}

export interface SymptomResponse {
  id: number
  recordId: number
  symptomName: string
  bodyPart: string | null
  severity: string | null
  durationDesc: string | null
  onsetTime: string | null
  notes: string | null
  createdAt: string
  updatedAt: string
}

export interface MedicalRecordResponse {
  id: number
  patientId: number
  caseCode: string
  chiefComplaint: string | null
  presentIllness: string | null
  pastHistory: string | null
  allergyHistory: string | null
  status: string
  createdBy: number
  createdAt: string
  updatedAt: string
  symptoms: SymptomResponse[]
}

export interface CreateSymptomRequest {
  recordId: number
  symptomName: string
  bodyPart?: string
  severity?: string
  durationDesc?: string
  onsetTime?: string
  notes?: string
}

export const medicalRecordApi = {
  create: (data: CreateMedicalRecordRequest) =>
    api.post<MedicalRecordResponse>('/v1/medical-records', data),

  getById: (id: number) =>
    api.get<MedicalRecordResponse>(`/v1/medical-records/${id}`),

  getByCaseCode: (caseCode: string) =>
    api.get<MedicalRecordResponse>(
      `/v1/medical-records/case-code/${encodeURIComponent(caseCode)}`,
    ),

  addSymptom: (
    recordId: number,
    data: CreateSymptomRequest,
  ) =>
    api.post<SymptomResponse>(
      `/v1/medical-records/${recordId}/symptoms`,
      data,
    ),

  getSymptoms: (recordId: number) =>
    api.get<SymptomResponse[]>(
      `/v1/medical-records/${recordId}/symptoms`,
    ),
}

// === Pre-consultation APIs ===

export interface CreatePreConsultationRequest {
  recordId: number
}

export interface PreConsultationResponse {
  id: number
  recordId: number
  patientId: number
  status: string
  initiatedBy: number
  reviewedBy: number | null
  reviewComment: string | null
  reviewedAt: string | null
  completedAt: string | null
  createdAt: string
  updatedAt: string
}

export const preConsultationApi = {
  create: (data: CreatePreConsultationRequest) =>
    api.post<PreConsultationResponse>(
      '/v1/pre-consultations',
      data,
    ),

  getById: (id: number) =>
    api.get<PreConsultationResponse>(
      `/v1/pre-consultations/${id}`,
    ),

  getByRecord: (recordId: number) =>
    api.get<PreConsultationResponse[]>(
      `/v1/pre-consultations/record/${recordId}`,
    ),
}
export default api
