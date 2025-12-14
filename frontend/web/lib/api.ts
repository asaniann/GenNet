import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const networkApi = {
  list: () => api.get('/api/v1/networks'),
  get: (id: string) => api.get(`/api/v1/networks/${id}`),
  create: (data: any) => api.post('/api/v1/networks', data),
  update: (id: string, data: any) => api.put(`/api/v1/networks/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/networks/${id}`),
}

export const workflowApi = {
  list: () => api.get('/api/v1/workflows'),
  get: (id: string) => api.get(`/api/v1/workflows/${id}`),
  create: (data: any) => api.post('/api/v1/workflows', data),
  getStatus: (id: string) => api.get(`/api/v1/workflows/${id}/status`),
  getResults: (id: string) => api.get(`/api/v1/workflows/${id}/results`),
}

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/api/v1/auth/token', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  register: (data: any) => api.post('/api/v1/auth/register', data),
  me: () => api.get('/api/v1/auth/me'),
  logout: () => api.post('/api/v1/auth/logout'),
}

export default api

