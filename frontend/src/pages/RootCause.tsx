import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Search, Play, AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import { runRCA, fetchAnomalies } from '../services/api'
import { RevenueBarChart } from '../components/Dashboard/Charts'
import toast from 'react-hot-toast'

export default function RootCause() {
  const [metric, setMetric] = useState('revenue')
  const [dateFrom, setDateFrom] = useState('2024-03-10')
  const [dateTo, setDateTo] = useState('2024-03-20')
  const [result, setResult] = useState<any>(null)

  const { data: anomalies } = useQuery({ queryKey: ['anomalies', 'all'], queryFn: () => fetchAnomalies('all') })

  const { mutate: runAnalysis, isPending } = useMutation({
    mutationFn: () => runRCA(metric, dateFrom, dateTo, 2.0),
    onSuccess: (data) => {
      setResult(data)
      toast.success('Root cause analysis complete!')
    },
    onError: () => toast.error('Analysis failed. Check your date range.'),
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Config Panel */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-red-glow/15 border border-red-glow/30 flex items-center justify-center">
            <Search size={16} className="text-red-glow" />
          </div>
          <div>
            <h3 className="text-white font-semibold">Root Cause Analysis Engine</h3>
            <p className="text-gray-500 text-xs">Slice across 6 dimensions to identify anomaly drivers</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Metric</label>
            <select
              value={metric}
              onChange={e => setMetric(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors"
            >
              <option value="revenue">Revenue</option>
              <option value="orders">Orders</option>
              <option value="sessions">Sessions</option>
              <option value="conversion_rate">Conversion Rate</option>
              <option value="nps">NPS</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Date From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={e => setDateFrom(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Date To</label>
            <input
              type="date"
              value={dateTo}
              onChange={e => setDateTo(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => runAnalysis()}
              disabled={isPending}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {isPending ? (
                <><Clock size={14} className="animate-spin" /> Analysing...</>
              ) : (
                <><Play size={14} /> Run Analysis</>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Known Anomalies */}
        <div className="glass-card p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle size={15} className="text-amber-glow" /> Known Anomalies
          </h3>
          <div className="space-y-3 overflow-y-auto max-h-[400px]">
            {(anomalies || []).map((a: any) => (
              <button
                key={a.event_id}
                onClick={() => { setMetric(a.metric); setDateFrom(a.detected_at?.split('T')[0] || dateFrom); setDateTo(a.detected_at?.split('T')[0] || dateTo) }}
                className="w-full text-left p-3 rounded-xl bg-white/3 hover:bg-white/6 border border-white/5 transition-all"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`badge badge-${a.severity}`}>{a.severity}</span>
                  <span className="text-white text-xs font-medium">{a.metric}</span>
                </div>
                <p className="text-gray-500 text-xs">{a.notes?.substring(0, 80)}...</p>
                <p className="text-gray-600 text-xs mt-1">{a.detected_at?.split('T')[0]}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Results */}
        <div className="xl:col-span-2 space-y-4">
          {!result && !isPending && (
            <div className="glass-card p-12 flex flex-col items-center text-center">
              <Search size={40} className="text-gray-700 mb-4" />
              <p className="text-gray-500">Configure a metric and date range, then run the analysis.</p>
              <p className="text-gray-600 text-sm mt-2">Try clicking one of the known anomalies on the left.</p>
            </div>
          )}

          {isPending && (
            <div className="glass-card p-12 flex flex-col items-center">
              <div className="w-12 h-12 border-2 border-cyan-glow/20 border-t-cyan-glow rounded-full animate-spin mb-4" />
              <p className="text-gray-400 text-sm">Slicing across dimensions…</p>
            </div>
          )}

          {result && !isPending && (
            <>
              {/* Summary */}
              <motion.div className="glass-card p-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <div className="flex items-start gap-3 mb-4">
                  <CheckCircle size={16} className="text-emerald-glow mt-0.5" />
                  <div>
                    <h3 className="text-white font-semibold">Analysis Summary</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">Confidence:</span>
                      <div className="flex-1 bg-white/5 rounded-full h-1.5 max-w-[120px]">
                        <div className="h-1.5 rounded-full bg-gradient-to-r from-cyan-glow to-emerald-glow"
                          style={{ width: `${(result.confidence_score || 0) * 100}%` }} />
                      </div>
                      <span className="text-xs text-cyan-glow font-semibold">{((result.confidence_score || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">{result.summary}</p>
              </motion.div>

              {/* Root Causes */}
              {result.root_causes?.length > 0 && (
                <motion.div className="glass-card p-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
                  <h3 className="text-white font-semibold mb-4">Top Contributing Factors</h3>
                  <div className="space-y-3">
                    {result.root_causes.slice(0, 5).map((rc: any, i: number) => (
                      <div key={i} className="flex items-center gap-4 p-3 rounded-xl bg-white/3 border border-white/5">
                        <span className="text-2xl font-bold text-gray-700 w-8">#{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm font-medium">
                            {rc.dimension}: <span className="text-cyan-glow">{rc.dimension_value}</span>
                          </p>
                          <p className="text-gray-500 text-xs mt-0.5">
                            Actual: {rc.actual?.toLocaleString()} · Expected: {rc.expected?.toLocaleString()}
                          </p>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="text-sm font-bold" style={{ color: rc.z_score < 0 ? '#FF4757' : '#00C896' }}>
                            {rc.z_score?.toFixed(1)}σ
                          </p>
                          <p className="text-xs text-gray-600">{rc.contribution_pct?.toFixed(1)}% contrib.</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {result.chart_spec && (
                    <div className="mt-5">
                      <RevenueBarChart
                        data={(result.chart_spec.data || []).slice(0, 10).map((d: any) => ({
                          name: d.dimension_value,
                          value: Math.abs(d.actual - d.expected),
                          color: d.z_score < 0 ? '#FF4757' : '#00C896',
                        }))}
                        height={200}
                      />
                    </div>
                  )}
                </motion.div>
              )}

              {/* Recommendations */}
              {result.recommended_actions?.length > 0 && (
                <motion.div className="glass-card p-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
                  <h3 className="text-white font-semibold mb-3">Recommended Actions</h3>
                  <div className="space-y-2">
                    {result.recommended_actions.map((action: string, i: number) => (
                      <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/3">
                        <span className="w-5 h-5 rounded-full bg-cyan-glow/20 text-cyan-glow text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                          {i + 1}
                        </span>
                        <p className="text-gray-300 text-sm leading-relaxed">{action}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
