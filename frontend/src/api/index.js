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
export const exportRecords = (data) => http.post('/api/search/export', data, { responseType: 'blob' })
export const getBrandTrends = (brand) => http.get('/api/dashboard/brand-trends', { params: { brand } })
export const uploadExcel = (formData) => http.post('/api/system/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const searchStandards = (params) => http.get('/api/search/standards', { params })
export const getStandardDetail = (params) => http.get('/api/search/standards/detail', { params })
// 新增：获取 PDF 页数以便生成压缩图像占位
export const getStandardPdfInfo = (params) => http.get(`/api/search/standards/file/${encodeURIComponent(params.brand_name)}/info`)
export const syncAllStandards = () => http.post('/api/import/sync-standards')
export const getStandardPdfs = () => http.get('/api/search/standards/pdfs')

export default http