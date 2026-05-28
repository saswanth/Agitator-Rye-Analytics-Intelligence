import axios from 'axios'

const BASE_URL = '/api'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120_000,
})

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const fetchKPIs = () => api.get('/dashboard/kpis').then(r => r.data)
export const fetchSalesTrend = (days = 90) => api.get(`/dashboard/sales-trend?days=${days}`).then(r => r.data)
export const fetchRevenueBreakdown = (days = 30) => api.get(`/dashboard/revenue-breakdown?days=${days}`).then(r => r.data)
export const fetchAnomalies = (status = 'open') => api.get(`/dashboard/anomalies?status=${status}`).then(r => r.data)
export const fetchPipelineHealth = () => api.get('/dashboard/pipeline-health').then(r => r.data)
export const fetchWebAnalytics = (days = 30) => api.get(`/dashboard/web-analytics?days=${days}`).then(r => r.data)

// ── Analytics ─────────────────────────────────────────────────────────────────

export const runQuery = (question: string) =>
  api.post('/analytics/query', { question, output_format: 'auto' }).then(r => r.data)

export const runRCA = (metric: string, dateFrom: string, dateTo: string, threshold = 2.0) =>
  api.post('/analytics/rca', { metric, date_from: dateFrom, date_to: dateTo, alert_threshold: threshold }).then(r => r.data)

export const runFinancial = (periodFrom: string, periodTo: string, scenario = 'base') =>
  api.post('/analytics/financial', { period_from: periodFrom, period_to: periodTo, include_forecast: true, scenario }).then(r => r.data)

export const runInsights = (persona = 'analyst', focusAreas: string[] = []) =>
  api.post('/analytics/insights', { persona, focus_areas: focusAreas }).then(r => r.data)

export const fetchMetricsSummary = (metric = 'revenue', period = '30d') =>
  api.get(`/analytics/metrics?metric=${metric}&period=${period}`).then(r => r.data)

// ── Pipeline ──────────────────────────────────────────────────────────────────

export const runPipeline = (pipelineName = 'default', targetTable = 'sales_transactions') =>
  api.post('/pipeline/run', { pipeline_name: pipelineName, target_table: targetTable, strategies: {} }).then(r => r.data)

export const fetchPipelineLogs = (limit = 50) =>
  api.get(`/pipeline/logs?limit=${limit}`).then(r => r.data)

export const fetchPipelineTables = () =>
  api.get('/pipeline/tables').then(r => r.data)

// ── Health ─────────────────────────────────────────────────────────────────

export const fetchHealth = () => api.get('/health', { baseURL: '' }).then(r => r.data)

// ── WebSocket helper ──────────────────────────────────────────────────────────

export const createChatWebSocket = (sessionId: string): WebSocket => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.hostname
  return new WebSocket(`${protocol}//${host}:8000/api/chat/ws/${sessionId}`)
}
