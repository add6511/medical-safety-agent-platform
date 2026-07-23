/**
 * 双客户端架构 — Spring Boot 后端 vs FastAPI AI 服务
 */
import axios, { type AxiosInstance } from 'axios'
import { env } from './env'

const T = 15_000

function auth(c: any) {
  const t = localStorage.getItem('accessToken')
  if (t && c.headers) c.headers.Authorization = `Bearer ${t}`
  return c
}

function onErr(err: any) {
  if (err.response?.status === 401) {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }
  return Promise.reject(err)
}

/** Spring Boot 后端 */
export const apiClient: AxiosInstance = axios.create({ baseURL: env.API_BASE_URL, timeout: T, headers: { 'Content-Type': 'application/json' } })
apiClient.interceptors.request.use(auth)
apiClient.interceptors.response.use(r => r, onErr)

/** FastAPI AI 服务 */
export const aiClient: AxiosInstance = axios.create({ baseURL: env.AI_API_BASE_URL, timeout: T, headers: { 'Content-Type': 'application/json' } })
aiClient.interceptors.request.use(auth)
aiClient.interceptors.response.use(r => r, onErr)
