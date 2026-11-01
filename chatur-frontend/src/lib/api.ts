import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, setTokens, logout } = useAuthStore.getState()
  if (!refreshToken) return null
  try {
    const res = await axios.post(`${api.defaults.baseURL}/auth/refresh`, {
      refresh_token: refreshToken,
    })
    setTokens(res.data.access_token, refreshToken)
    return res.data.access_token
  } catch {
    logout()
    return null
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    const isAuthCall = original?.url?.includes('/auth/')
    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true
      refreshing = refreshing ?? refreshAccessToken().finally(() => (refreshing = null))
      const token = await refreshing
      if (token) {
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      }
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api