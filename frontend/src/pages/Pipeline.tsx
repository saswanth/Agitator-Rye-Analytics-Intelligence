import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Database, Play, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react'
import { fetchPipelineHealth, fetchPipelineLogs, runPipeline, fetchPipelineTables } from '../services/api'
import toast from 'react-hot-toast'

const STATUS_ICONS: Record<string, any> = {
  completed: <CheckCircle size={13} className="text-emerald-glow" />,
  failed: <XCircle size={13} className="text-red-glow" />,
  running: <Clock size={13} className="text-amber-glow animate-pulse" />,
  partial: <AlertCircle size={13} className="text-amber-glow" />,
}

export default function Pipeline() {
  const [selectedTable, setSelectedTable] = useState('sales_transactions')
  const [rowLimit, setRowLimit] = useState(10000)
  const [runResult, setRunResult] = useState<any>(null)

  const { data: health, refetch: refetchHealth } = useQuery({ queryKey: ['pipeline-health'], queryFn: fetchPipelineHealth })
  const { data: logs, refetch: refetchLogs } = useQuery({ queryKey: ['pipeline-logs'], queryFn: () => fetchPipelineLogs(), refetchInterval: 15_000 })
  const { data: tables } = useQuery({ queryKey: ['pipeline-tables'], queryFn: () => fetchPipelineTables() })

  const { mutate: triggerRun, isPending } = useMutation({
    mutationFn: () => runPipeline('default', selectedTable),
    onSuccess: (data) => {
      setRunResult(data)
      toast.success(`Pipeline completed! Quality: ${data.quality_score?.toFixed(1)}/100`)
      refetchHealth()
      refetchLogs()
    },
    onError: () => toast.error('Pipeline run failed.'),
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Controls */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-purple-glow/15 border border-purple-glow/30 flex items-center justify-center">
            <Database size={16} className="text-purple-glow" />
          </div>
          <div>
            <h3 className="text-white font-semibold">Data Pipeline Manager</h3>
            <p className="text-gray-500 text-xs">6-stage pipeline: Ingest → Schema → Quality → Clean → Validate → Load</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Target Table</label>
            <select value={selectedTable} onChange={e => setSelectedTable(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors">
              {(Array.isArray(tables) ? tables : ['sales_transactions', 'customers', 'products', 'daily_metrics', 'financial_data', 'web_analytics']).map((t: string) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Row Limit</label>
            <input type="number" value={rowLimit} onChange={e => setRowLimit(Number(e.target.value))} min={100} max={200000} step={1000}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors" />
          </div>
          <div className="flex items-end">
            <button onClick={() => triggerRun()} disabled={isPending} className="btn-primary w-full flex items-center justify-center gap-2">
              {isPending ? <><Clock size={14} className="animate-spin" />Running Pipeline...</> : <><Play size={14} />Run Pipeline</>}
            </button>
          </div>
        </div>
      </div>

      {/* Pipeline Stages visualiser (live run) */}
      {(isPending || runResult) && (
        <motion.div className="glass-card p-6" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <h3 className="text-white font-semibold mb-4">Pipeline Stages</h3>
          <div className="flex items-center gap-2 flex-wrap">
            {['ingest', 'schema_check', 'quality_check', 'clean', 'validate', 'load'].map((stage, i) => {
              const stageResult = runResult?.stages?.find((s: any) => s.stage === stage)
              const isActive = isPending && !stageResult
              return (
                <div key={stage} className="flex items-center gap-2">
                  <div className={`px-3 py-2 rounded-xl border text-xs font-medium flex items-center gap-1.5 transition-all ${
                    stageResult?.status === 'completed' ? 'bg-emerald-glow/10 border-emerald-glow/30 text-emerald-glow' :
                    stageResult?.status === 'failed' ? 'bg-red-glow/10 border-red-glow/30 text-red-glow' :
                    isActive && i === (runResult?.stages?.length ?? 0) ? 'bg-amber-glow/10 border-amber-glow/30 text-amber-glow' :
                    'bg-white/5 border-white/5 text-gray-500'
                  }`}>
                    {stageResult ? STATUS_ICONS[stageResult.status] : null}
                    {stage.replace(/_/g, ' ')}
                    {stageResult && <span className="text-[10px] opacity-60 ml-1">{stageResult.duration_ms}ms</span>}
                  </div>
                  {i < 5 && <div className="w-4 h-px bg-white/10" />}
                </div>
              )
            })}
          </div>

          {runResult && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
              <div className="p-4 rounded-xl bg-white/3 border border-white/5">
                <p className="text-gray-500 text-xs">Quality Score</p>
                <p className="text-2xl font-bold text-gradient mt-1">{runResult.quality_score?.toFixed(1)}</p>
                <div className="mt-2 w-full bg-white/5 rounded-full h-1.5">
                  <div className="h-1.5 rounded-full bg-gradient-to-r from-cyan-glow to-emerald-glow"
                    style={{ width: `${runResult.quality_score}%` }} />
                </div>
              </div>
              <div className="p-4 rounded-xl bg-white/3 border border-white/5">
                <p className="text-gray-500 text-xs">Rows Loaded</p>
                <p className="text-2xl font-bold text-white mt-1">{runResult.rows_loaded?.toLocaleString()}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/3 border border-white/5">
                <p className="text-gray-500 text-xs">Issues Found</p>
                <p className="text-2xl font-bold text-amber-glow mt-1">{runResult.issues_found?.length ?? 0}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/3 border border-white/5">
                <p className="text-gray-500 text-xs">Duration</p>
                <p className="text-2xl font-bold text-purple-glow mt-1">{runResult.total_duration_ms}ms</p>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Health + Logs */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Health summary */}
        <div className="glass-card p-6">
          <h3 className="text-white font-semibold mb-4">Overall Health</h3>
          {health ? (
            <div className="space-y-4">
              <div className="text-center py-2">
                <p className="text-5xl font-bold text-gradient">{health.overall_score?.toFixed(1)}</p>
                <p className="text-gray-500 text-xs mt-1">Quality Score / 100</p>
              </div>
              <div className="w-full bg-white/5 rounded-full h-2">
                <div className="h-2 rounded-full bg-gradient-to-r from-purple-glow to-cyan-glow"
                  style={{ width: `${health.overall_score}%` }} />
              </div>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div className="p-2 rounded-lg bg-white/3">
                  <p className="text-emerald-glow font-semibold">{health.success_rate?.toFixed(1)}%</p>
                  <p className="text-gray-600 text-xs">Success Rate</p>
                </div>
                <div className="p-2 rounded-lg bg-white/3">
                  <p className="text-white font-semibold">{health.total_runs}</p>
                  <p className="text-gray-600 text-xs">Total Runs</p>
                </div>
              </div>
            </div>
          ) : <div className="skeleton h-48" />}
        </div>

        {/* Logs table */}
        <div className="xl:col-span-3 glass-card p-6">
          <h3 className="text-white font-semibold mb-4">Recent Pipeline Runs</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left px-3 py-2 text-gray-500 text-xs font-medium">Run ID</th>
                  <th className="text-left px-3 py-2 text-gray-500 text-xs font-medium">Table</th>
                  <th className="text-left px-3 py-2 text-gray-500 text-xs font-medium">Stage</th>
                  <th className="text-left px-3 py-2 text-gray-500 text-xs font-medium">Status</th>
                  <th className="text-right px-3 py-2 text-gray-500 text-xs font-medium">Quality</th>
                  <th className="text-right px-3 py-2 text-gray-500 text-xs font-medium">Rows</th>
                  <th className="text-right px-3 py-2 text-gray-500 text-xs font-medium">Started</th>
                </tr>
              </thead>
              <tbody>
                {(Array.isArray(logs) ? logs : []).slice(0, 20).map((log: any) => (
                  <tr key={log.id} className="border-b border-white/3 hover:bg-white/2 transition-colors">
                    <td className="px-3 py-2.5 text-gray-500 text-xs font-mono">{log.run_id?.slice(0, 8)}</td>
                    <td className="px-3 py-2.5 text-gray-300 text-xs">{log.table_name}</td>
                    <td className="px-3 py-2.5">
                      <span className="badge badge-info">{log.stage}</span>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-1.5">
                        {STATUS_ICONS[log.status] || null}
                        <span className={`text-xs font-medium ${
                          log.status === 'completed' ? 'text-emerald-glow' :
                          log.status === 'failed' ? 'text-red-glow' : 'text-amber-glow'
                        }`}>{log.status}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      {log.quality_score !== null && (
                        <span className="text-xs font-semibold text-cyan-glow">{log.quality_score?.toFixed(1)}</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-right text-gray-400 text-xs">{log.rows_processed?.toLocaleString()}</td>
                    <td className="px-3 py-2.5 text-right text-gray-600 text-xs">
                      {log.started_at ? new Date(log.started_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
                {(!logs || !Array.isArray(logs) || (logs as any[]).length === 0) && (
                  <tr><td colSpan={7} className="px-3 py-8 text-center text-gray-600 text-sm">No pipeline runs yet. Click Run Pipeline above.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
