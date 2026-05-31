import axios, { type InternalAxiosRequestConfig } from 'axios'

import { logger } from '../utils/logger'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const http = axios.create({
  baseURL: apiBaseUrl,
})

type TimedRequestConfig = InternalAxiosRequestConfig & {
  metadata?: {
    startedAt: number
  }
}

export function getToken(): string | null {
  return sessionStorage.getItem('access_token')
}

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  ;(config as TimedRequestConfig).metadata = { startedAt: performance.now() }
  logger.info('API request started', {
    method: config.method?.toUpperCase(),
    url: config.url,
  })
  return config
})

http.interceptors.response.use(
  (response) => {
    const startedAt = (response.config as TimedRequestConfig).metadata?.startedAt
    const durationMs = startedAt ? Math.round(performance.now() - startedAt) : undefined
    logger.info('API request completed', {
      method: response.config.method?.toUpperCase(),
      url: response.config.url,
      status: response.status,
      durationMs,
    })
    return response
  },
  (error) => {
    const config = error.config || {}
    const startedAt = (config as TimedRequestConfig).metadata?.startedAt
    const durationMs = startedAt ? Math.round(performance.now() - startedAt) : undefined
    logger.error('API request failed', {
      method: config.method?.toUpperCase(),
      url: config.url,
      status: error.response?.status,
      message: error.response?.data?.message || error.message,
      durationMs,
    })
    return Promise.reject(error)
  },
)

