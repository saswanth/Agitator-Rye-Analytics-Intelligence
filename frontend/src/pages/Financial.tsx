import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { DollarSign, TrendingUp, Play, Clock, ArrowUpRight, ArrowDownRight, Download } from 'lucide-react'
import * as XLSX from 'xlsx'
import { runFinancial } from '../services/api'
import { SimpleLineChart, RevenueBarChart } from '../components/Dashboard/Charts'
import toast from 'react-hot-toast'

const SCENARIOS = [
  { value: 'base', label: 'Base Case', desc: 'Expected trajectory' },
  { value: 'bull', label: 'Bull Case', desc: 'Optimistic upside (+20%)' },
  { value: 'bear', label: 'Bear Case', desc: 'Pessimistic downside (-20%)' },
]

function RatioCard({ label, value, target, unit = '' }: any) {
  const pct = target ? Math.min(100, (value / target) * 100) : null
  const good = value >= 0
  return (
    <div className="p-4 rounded-xl bg-white/3 border border-white/5">
      <p className="text-gray-500 text-xs mb-2">{label}</p>
      <div className="flex items-end justify-between">
        <span className="text-white font-bold text-xl">{value?.toFixed(2)}{unit}</span>
        {good ? <ArrowUpRight size={14} className="text-emerald-glow" /> : <ArrowDownRight size={14} className="text-red-glow" />}
      </div>
      {pct !== null && (
        <div className="mt-2 w-full bg-white/5 rounded-full h-1">
          <div className="h-1 rounded-full bg-gradient-to-r from-purple-glow to-cyan-glow" style={{ width: `${pct}%` }} />
        </div>
      )}
    </div>
  )
}

export default function Financial() {
  const [periodFrom, setPeriodFrom] = useState('2023-01-01')
  const [periodTo, setPeriodTo] = useState('2024-06-30')
  const [scenario, setScenario] = useState('base')
  const [result, setResult] = useState<any>(null)

  const { mutate: runAnalysis, isPending } = useMutation({
    mutationFn: () => runFinancial(periodFrom, periodTo, scenario),
    onSuccess: (data) => { setResult(data); toast.success('Financial analysis ready!') },
    onError: () => toast.error('Analysis failed. Adjust the date range.'),
  })

  function downloadXLSX() {
    if (!result) return
    const wb = XLSX.utils.book_new()

    // Revenue Trend sheet
    if (result.revenue_trend?.length) {
      const ws1 = XLSX.utils.json_to_sheet(result.revenue_trend)
      XLSX.utils.book_append_sheet(wb, ws1, 'Revenue Trend')
    }

    // Forecast sheet
    if (result.forecast?.revenue?.length) {
      const ws2 = XLSX.utils.json_to_sheet(result.forecast.revenue)
      XLSX.utils.book_append_sheet(wb, ws2, 'Forecast')
    }

    // Margin Trend sheet
    if (result.margin_trend?.length) {
      const ws3 = XLSX.utils.json_to_sheet(result.margin_trend)
      XLSX.utils.book_append_sheet(wb, ws3, 'Margin Trend')
    }

    // Key Ratios sheet
    if (result.financial_ratios) {
      const ratioRows = Object.entries(result.financial_ratios).map(([k, v]) => ({ metric: k, value: v }))
      const ws4 = XLSX.utils.json_to_sheet(ratioRows)
      XLSX.utils.book_append_sheet(wb, ws4, 'Financial Ratios')
    }

    // Risks & Opportunities sheet
    const roRows = [
      ...(result.risk_factors || []).map((r: string) => ({ type: 'Risk', item: r })),
      ...(result.opportunities || []).map((o: string) => ({ type: 'Opportunity', item: o })),
    ]
    if (roRows.length) {
      const ws5 = XLSX.utils.json_to_sheet(roRows)
      XLSX.utils.book_append_sheet(wb, ws5, 'Risks & Opportunities')
    }

    const filename = `financial-report-${periodFrom}-to-${periodTo}-${scenario}.xlsx`
    XLSX.writeFile(wb, filename)
    toast.success('Report downloaded!')
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Config */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-emerald-glow/15 border border-emerald-glow/30 flex items-center justify-center">
            <DollarSign size={16} className="text-emerald-glow" />
          </div>
          <div>
            <h3 className="text-white font-semibold">Financial Analysis Engine</h3>
            <p className="text-gray-500 text-xs">12+ financial ratios + Holt-Winters forecasting</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Period From</label>
            <input type="date" value={periodFrom} onChange={e => setPeriodFrom(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors" />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Period To</label>
            <input type="date" value={periodTo} onChange={e => setPeriodTo(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors" />
          </div>
          <div>
            <label className="text-xs text-gray-500 font-medium block mb-1.5">Forecast Scenario</label>
            <select value={scenario} onChange={e => setScenario(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-gray-200 text-sm outline-none focus:border-cyan-glow/40 transition-colors">
              {SCENARIOS.map(s => <option key={s.value} value={s.value}>{s.label} — {s.desc}</option>)}
            </select>
          </div>
          <div className="flex items-end gap-2">
            <button onClick={() => runAnalysis()} disabled={isPending} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {isPending ? <><Clock size={14} className="animate-spin" />Analysing...</> : <><Play size={14} />Run Analysis</>}
            </button>
            {result && (
              <button onClick={downloadXLSX} className="px-3 py-2.5 rounded-xl border border-emerald-glow/30 bg-emerald-glow/10 text-emerald-glow hover:bg-emerald-glow/20 transition-colors flex items-center gap-1.5 text-sm whitespace-nowrap">
                <Download size={14} /> XLSX
              </button>
            )}
          </div>
        </div>
      </div>

      {!result && !isPending && (
        <div className="glass-card p-16 flex flex-col items-center text-center">
          <DollarSign size={40} className="text-gray-700 mb-4" />
          <p className="text-gray-500">Set a date range and scenario, then run the analysis.</p>
        </div>
      )}

      {isPending && (
        <div className="glass-card p-16 flex flex-col items-center">
          <div className="w-12 h-12 border-2 border-emerald-glow/20 border-t-emerald-glow rounded-full animate-spin mb-4" />
          <p className="text-gray-400 text-sm">Computing financial ratios & forecast…</p>
        </div>
      )}

      {result && !isPending && (
        <>
          {/* Revenue trend */}
          {result.revenue_trend && (
            <motion.div className="glass-card p-6" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h3 className="text-white font-semibold">Revenue Trend & Forecast</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="badge badge-success">Scenario: {scenario}</span>
                    <span className="text-gray-500 text-xs">CAGR: {result.growth_metrics?.revenue_cagr?.toFixed(1)}%</span>
                  </div>
                </div>
                <TrendingUp size={16} className="text-emerald-glow" />
              </div>
              <SimpleLineChart
                data={[
                  ...(result.revenue_trend || []).map((d: any) => ({ name: d.period, value: d.revenue })),
                  ...(result.forecast?.revenue || []).map((d: any) => ({ name: d.period + ' (F)', value: d.forecast, forecast: true })),
                ]}
                height={240}
                color="#00C896"
              />
            </motion.div>
          )}

          {/* Key Ratios */}
          {result.financial_ratios && (
            <motion.div className="glass-card p-6" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <h3 className="text-white font-semibold mb-4">Financial Ratios</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
                {Object.entries(result.financial_ratios || {}).slice(0, 12).map(([k, v]) => (
                  <RatioCard key={k} label={k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} value={v} />
                ))}
              </div>
            </motion.div>
          )}

          {/* Risks & Opportunities */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {result.risk_factors?.length > 0 && (
              <motion.div className="glass-card p-6" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-red-glow" /> Risk Factors
                </h3>
                <div className="space-y-2">
                  {result.risk_factors.map((r: string, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-red-glow/5 border border-red-glow/10">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-glow mt-1.5 flex-shrink-0" />
                      <p className="text-gray-300 text-sm">{r}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {result.opportunities?.length > 0 && (
              <motion.div className="glass-card p-6" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-glow" /> Opportunities
                </h3>
                <div className="space-y-2">
                  {result.opportunities.map((o: string, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-emerald-glow/5 border border-emerald-glow/10">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-glow mt-1.5 flex-shrink-0" />
                      <p className="text-gray-300 text-sm">{o}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>

          {/* Narrative */}
          {result.narrative && (
            <motion.div className="glass-card p-6" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
              <h3 className="text-white font-semibold mb-3">AI Financial Narrative</h3>
              <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">{result.narrative}</p>
            </motion.div>
          )}
        </>
      )}
    </div>
  )
}
