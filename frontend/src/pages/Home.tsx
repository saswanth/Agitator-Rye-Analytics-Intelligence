import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { AlertTriangle, TrendingUp, Activity, Database } from 'lucide-react'
import KPICard from '../components/Dashboard/KPICard'
import { MultiSeriesAreaChart, RevenueBarChart, DonutChart } from '../components/Dashboard/Charts'
import {
  fetchKPIs, fetchSalesTrend, fetchRevenueBreakdown,
  fetchAnomalies, fetchPipelineHealth, fetchWebAnalytics
} from '../services/api'

function LoadingCard({ className = '' }: { className?: string }) {
  return <div className={`skeleton h-32 ${className}`} />
}

export default function Home() {
  const { data: kpisData, isLoading: kpiLoading } = useQuery({ queryKey: ['kpis'], queryFn: fetchKPIs, refetchInterval: 60_000 })
  const { data: trendData, isLoading: trendLoading } = useQuery({ queryKey: ['sales-trend', 90], queryFn: () => fetchSalesTrend(90) })
  const { data: breakdown, isLoading: breakdownLoading } = useQuery({ queryKey: ['breakdown'], queryFn: () => fetchRevenueBreakdown(30) })
  const { data: anomalies } = useQuery({ queryKey: ['anomalies'], queryFn: () => fetchAnomalies('all'), refetchInterval: 30_000 })
  const { data: pipelineHealth } = useQuery({ queryKey: ['pipeline-health'], queryFn: fetchPipelineHealth })
  const { data: webData } = useQuery({ queryKey: ['web-analytics'], queryFn: () => fetchWebAnalytics(30) })

  const kpis = kpisData?.kpis || []

  return (
    <div className="space-y-6 animate-fade-in">
      {/* KPI Row */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">Key Performance Indicators</h3>
          <span className="text-xs text-gray-600">Last 30 days vs prior 30 days</span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {kpiLoading
            ? Array.from({ length: 6 }).map((_, i) => <LoadingCard key={i} />)
            : kpis.map((kpi: any, i: number) => (
              <KPICard
                key={kpi.title}
                title={kpi.title}
                value={kpi.formatted_value}
                delta={kpi.delta}
                deltaLabel={kpi.delta_label}
                trend={kpi.trend}
                icon={kpi.icon}
                delay={i * 0.06}
              />
            ))
          }
        </div>
      </section>

      {/* Main Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Revenue/Orders/Sessions trend */}
        <motion.div
          className="glass-card p-6 xl:col-span-2"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
        >
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-white font-semibold">Revenue, Orders & Sessions</h3>
              <p className="text-gray-500 text-xs mt-0.5">90-day time series</p>
            </div>
            <TrendingUp size={16} className="text-cyan-glow" />
          </div>
          {trendLoading ? (
            <div className="skeleton h-64" />
          ) : (
            <MultiSeriesAreaChart series={trendData?.series || []} height={264} />
          )}
        </motion.div>

        {/* Revenue by Region */}
        <motion.div
          className="glass-card p-6"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
        >
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-white font-semibold">Revenue by Region</h3>
              <p className="text-gray-500 text-xs mt-0.5">Last 30 days</p>
            </div>
          </div>
          {breakdownLoading ? (
            <div className="skeleton h-64" />
          ) : (
            <DonutChart data={breakdown?.by_region || []} height={220} />
          )}
        </motion.div>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Revenue by Channel */}
        <motion.div
          className="glass-card p-6"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}
        >
          <h3 className="text-white font-semibold mb-1">Revenue by Channel</h3>
          <p className="text-gray-500 text-xs mb-4">Last 30 days</p>
          {breakdownLoading ? <div className="skeleton h-48" /> : (
            <RevenueBarChart data={breakdown?.by_channel || []} height={200} color="#7B3FE4" />
          )}
        </motion.div>

        {/* Anomaly Alerts */}
        <motion.div
          className="glass-card p-6"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-semibold">Anomaly Alerts</h3>
            <AlertTriangle size={14} className="text-amber-glow" />
          </div>
          <div className="space-y-3 overflow-y-auto max-h-52">
            {(anomalies || []).slice(0, 5).map((a: any) => (
              <div key={a.event_id} className="flex items-start gap-3 p-3 rounded-xl bg-white/3 border border-white/5">
                <span className={`badge badge-${a.severity} flex-shrink-0 mt-0.5`}>{a.severity}</span>
                <div className="min-w-0">
                  <p className="text-white text-xs font-medium truncate">{a.metric}</p>
                  <p className="text-gray-500 text-xs mt-0.5">z={a.z_score?.toFixed(1)} · {a.dimension}: {a.dimension_value}</p>
                </div>
              </div>
            ))}
            {(!anomalies || anomalies.length === 0) && (
              <p className="text-gray-600 text-sm text-center py-4">No active anomalies</p>
            )}
          </div>
        </motion.div>

        {/* Pipeline Health */}
        <motion.div
          className="glass-card p-6"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-semibold">Pipeline Health</h3>
            <Database size={14} className="text-purple-glow" />
          </div>
          {pipelineHealth ? (
            <div className="space-y-4">
              {/* Score */}
              <div className="flex items-center justify-between">
                <span className="text-gray-400 text-sm">Quality Score</span>
                <span className="text-2xl font-bold text-gradient">
                  {pipelineHealth.overall_score?.toFixed(1)}
                </span>
              </div>
              <div className="w-full bg-white/5 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-gradient-to-r from-emerald-glow to-cyan-glow transition-all"
                  style={{ width: `${pipelineHealth.overall_score}%` }}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-white/3 border border-white/5">
                  <p className="text-gray-500 text-xs">Success Rate</p>
                  <p className="text-white font-semibold text-sm mt-1">{pipelineHealth.success_rate?.toFixed(1)}%</p>
                </div>
                <div className="p-3 rounded-xl bg-white/3 border border-white/5">
                  <p className="text-gray-500 text-xs">Total Runs</p>
                  <p className="text-white font-semibold text-sm mt-1">{pipelineHealth.total_runs}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="skeleton h-36" />
          )}
        </motion.div>
      </div>

      {/* Web Analytics strip */}
      {webData && (
        <motion.div
          className="glass-card p-6"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
        >
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-white font-semibold">Web Analytics</h3>
              <p className="text-gray-500 text-xs mt-0.5">Sessions & Bounce Rate — last 30 days</p>
            </div>
            <Activity size={14} className="text-cyan-glow" />
          </div>
          <MultiSeriesAreaChart series={webData.series || []} height={180} showLegend={false} />
        </motion.div>
      )}
    </div>
  )
}
