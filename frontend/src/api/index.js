import axios from 'axios'

const http = axios.create({
  baseURL: '',
  timeout: 600000
})

http.interceptors.request.use(
  (config) => {
    console.log('[HTTP REQUEST]', config.method?.toUpperCase(), config.url, config.data || config.params || '')
    return config
  },
  (error) => {
    console.error('[HTTP REQUEST ERROR]', error)
    return Promise.reject(error)
  }
)

http.interceptors.response.use(
  (response) => {
    console.log('[HTTP RESPONSE]', response.config.url, response.status, response.data)
    return response
  },
  (error) => {
    console.error('[HTTP RESPONSE ERROR]', error)

    if (error.response) {
      console.error('[HTTP RESPONSE ERROR DATA]', error.response.data)
      console.error('[HTTP RESPONSE STATUS]', error.response.status)
    } else if (error.request) {
      console.error('[HTTP NO RESPONSE]', error.request)
    } else {
      console.error('[HTTP CONFIG ERROR]', error.message)
    }

    return Promise.reject(error)
  }
)

export const getOverview = () => http.get('/api/dashboard/overview')
export const getSystemStatus = () => http.get('/api/system/status')
export const pingImport = () => http.get('/api/import/ping')
export const syncAllExcels = () => http.post('/api/import/sync-all')
export const searchRecords = (params) => http.get('/api/search', { params })
export const getRecordDetail = (params) => http.get('/api/search/detail', { params })
export const getSettings = () => http.get('/api/system/settings')
export const saveSettings = (data) => http.post('/api/system/settings', data)

export default http