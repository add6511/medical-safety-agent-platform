export const env = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1',
  AI_API_BASE_URL: import.meta.env.VITE_AI_API_BASE_URL || 'http://localhost:8000/api/v1',
  USE_MOCK: import.meta.env.VITE_USE_MOCK !== 'false',
}
