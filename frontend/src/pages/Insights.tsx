import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Lightbulb, Play, Clock, ChevronDown, ChevronUp, TrendingUp } from 'lucide-react'
import { runInsights } from '../services/api'
import { SimpleLineChart, RevenueBarChart } from '../components/Dashboard/Charts'
import toast from 'react-hot-toast'

const PERSONAS = [
  { value: 'exec', label: 'Executive', desc: 'High-level strategic summary', color: '#FFB800' },
  { value: 'analyst', label: 'Analyst', desc: 'Deep analytical narrative', color: '#00D4FF' },
  { value: 'engineer', label: 'Engineer', desc: 'Technical data quality report', color: '#7B3FE4' },
]

function InsightSection({ section, delay = 0 }: { section: any; delay?: number }) {
  const [expanded, setExpanded] = useState(true)

  return (
    <motion.div
      className="glass-card overflow-hidden"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-5 hover:bg-white/2 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-glow/20 to-purple-glow/20 flex items-center justify-center">
            <TrendingUp size={14} className="text-cyan-glow" />
          </div>
          <div className="text-left">
            <p className="text-white font-semibold text-sm">{section.title}</p>
            <p className="text-gray-500 text-xs">{section.period}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {section.trend && (
            <span className={`badge ${section.trend === 'increasing' ? 'badge-success' : section.trend === 'decreasing' ? 'badge-error' : 'badge-warning'}`}>
              {section.trend}
            </span>
          )}
          {section.change_pct !== undefined && (
            <span className={`text-sm font-bold ${section.change_pct >= 0 ? 'text-emerald-glow' : 'text-red-glow'}`}>
              {section.change_pct >= 0 ? '+' : ''}{section.change_pct?.toFixed(1)}%
            </span>
          )}
          {expanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-4 border-t border-white/5">
              <p className="text-gray-300 text-sm leading-relaxed mt-4">{section.narrative}</p>

              {section.chart_spec?.data && (
                <div className="mt-2">
                  {section.chart_spec.type === 'bar' ? (
                    <RevenueBarChart
                      data={section.chart_spec.data.slice(0, 20).map((d: any) => ({
                        name: String(Object.values(d)[0] ?? ''),
                        value: Number(Object.values(d)[1] ?? 0),
                      }))}
                      height={180}
                    />
                  ) : (
                    <SimpleLineChart
                      data={section.chart_spec.data.slice(0, 60).map((d: any) => ({
                        name: String(d.date || Object.values(d)[0] || ''),
                        value: Number(d.value || Object.values(d)[1] || 0),
                      }))}
                      height={180}
                    />
                  )}
                </div>
              )}

              {section.key_findings?.length > 0 && (
                <div>
                  <p className="text-gray-500 text-xs font-semibold uppercase tracking-wider mb-2">Key Findings</p>
                  <div className="space-y-1.5">
                    {section.key_findings.map((f: string, i: number) => (
                      <div key={i} className="flex gap-2">
                        <span className="text-cyan-glow text-xs font-bold mt-0.5">→</span>
                        <p className="text-gray-400 text-xs leading-relaxed">{f}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function Insights() {
  const [persona, setPersona] = useState('analyst')
  const [days, setDays] = useState(90)
  const [result, setResult] = useState<any>(null)

  const { mutate: generate, isPending } = useMutation({
    mutationFn: () => runInsights(persona, []),
    onSuccess: (data) => { setResult(data); toast.success('Insights generated!') },
    onError: () => toast.error('Failed to generate insights.'),
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Config */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-amber-glow/15 border border-amber-glow/30 flex items-center justify-center">
            <Lightbulb size={16} className="text-amber-glow" />
          </div>
          <div>
            <h3 className="text-white font-semibold">Auto Insight Generation</h3>
            <p className="text-gray-500 text-xs">Mann-Kendall trend + week-over-week analysis with AI narrative</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Persona selector */}
          <div className="md:col-span-2">
            <label className="text-xs text-gray-500 font-medium block mb-2">Report Persona</label>
            <div className="grid grid-cols-3 gap-3">
              {PERSONAS.map(p => (
                <button
                  key={p.value}
                  onClick={() => setPersona(p.value)}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    persona === p.value
                      ? 'border-cyan-glow/40 bg-cyan-glow/8'
                      : 'border-white/5 bg-white/3 hover:bg-white/5'
                  }`}
                >
                  <div className="w-6 h-6 rounded-lg mb-2 flex items-center justify-center" style={{ background: `${p.color}20`, border: `1px solid ${p.color}40` }}>
                    <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
                  </div>
                  <p className="text-white text-sm font-medium">{p.label}</p>
                  <p className="text-gray-500 text-xs mt-0.5">{p.desc}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs text-gray-500 font-medium block mb-1.5">Analysis Window (Days)</label>
              <input type="number" value={days} onChange={e => setDays(Number(e.target.value))} min={14} max={365} step={7}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors" />
            </div>
            <button onClick={() => generate()} disabled={isPending} className="btn-primary w-full flex items-center justify-center gap-2">
              {isPending ? <><Clock size={14} className="animate-spin" />Generating...</> : <><Play size={14} />Generate Insights</>}
            </button>
          </div>
        </div>
      </div>

      {/* Placeholder */}
      {!result && !isPending && (
        <div className="glass-card p-16 flex flex-col items-center text-center">
          <Lightbulb size={40} className="text-gray-700 mb-4" />
          <p className="text-gray-500">Select a persona and analysis window, then generate insights.</p>
        </div>
      )}

      {isPending && (
        <div className="glass-card p-16 flex flex-col items-center">
          <div className="w-12 h-12 border-2 border-amber-glow/20 border-t-amber-glow rounded-full animate-spin mb-4" />
          <p className="text-gray-400 text-sm">Running trend analysis & generating narrative…</p>
        </div>
      )}

      {result && !isPending && (
        <>
          {/* Executive Summary */}
          <motion.div className="glass-card p-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="flex items-center gap-2 mb-3">
              <span className="badge badge-warning uppercase">Executive Summary</span>
              <span className="text-gray-500 text-xs">· {persona} view · last {days} days</span>
            </div>
            <p className="text-gray-200 text-sm leading-relaxed">{result.executive_summary}</p>
          </motion.div>

          {/* Sections */}
          <div className="space-y-4">
            {(result.insights || []).map((section: any, i: number) => (
              <InsightSection key={i} section={section} delay={i * 0.08} />
            ))}
          </div>

          {/* Recommended Actions */}
          {result.recommended_actions?.length > 0 && (
            <motion.div className="glass-card p-6" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
              <h3 className="text-white font-semibold mb-4">Recommended Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.recommended_actions.map((a: string, i: number) => (
                  <div key={i} className="flex gap-3 p-4 rounded-xl bg-amber-glow/5 border border-amber-glow/10">
                    <span className="w-6 h-6 rounded-lg bg-amber-glow/20 text-amber-glow text-xs font-bold flex items-center justify-center flex-shrink-0">
                      {i + 1}
                    </span>
                    <p className="text-gray-300 text-sm">{a}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </>
      )}
    </div>
  )
}
