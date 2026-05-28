import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell
} from 'recharts'

interface ChartDataPoint {
  date: string
  value: number
  [key: string]: string | number
}

interface Series {
  name: string
  data: ChartDataPoint[]
  color: string
}

// ── Custom Tooltip ─────────────────────────────────────────────────────────────

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card p-3 shadow-xl border border-white/10 min-w-[160px]">
      <p className="text-gray-400 text-xs mb-2">{label}</p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-xs text-gray-300">
            <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
            {entry.name}
          </span>
          <span className="text-xs font-semibold text-white">
            {typeof entry.value === 'number' && entry.value > 10000
              ? `$${(entry.value / 1000).toFixed(1)}K`
              : typeof entry.value === 'number'
              ? entry.value.toLocaleString()
              : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

// ── Multi-Series Area Chart ────────────────────────────────────────────────────

interface MultiSeriesAreaChartProps {
  series: Series[]
  height?: number
  showLegend?: boolean
}

export function MultiSeriesAreaChart({ series, height = 280, showLegend = true }: MultiSeriesAreaChartProps) {
  // Merge all series into one dataset keyed by date
  const dateMap = new Map<string, Record<string, number>>()
  series.forEach(s => {
    s.data.forEach(point => {
      if (!dateMap.has(point.date)) dateMap.set(point.date, { date: point.date as any })
      dateMap.get(point.date)![s.name] = point.value
    })
  })
  const mergedData = Array.from(dateMap.values()).sort((a, b) => String(a.date).localeCompare(String(b.date)))
  // Sample every N points for performance
  const step = Math.max(1, Math.floor(mergedData.length / 120))
  const sampled = mergedData.filter((_, i) => i % step === 0)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={sampled} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
        <defs>
          {series.map(s => (
            <linearGradient key={s.name} id={`grad-${s.name}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={s.color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={s.color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: '#6B7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: '#6B7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => v >= 1000000 ? `${(v/1000000).toFixed(1)}M` : v >= 1000 ? `${(v/1000).toFixed(0)}K` : v}
        />
        <Tooltip content={<CustomTooltip />} />
        {showLegend && <Legend wrapperStyle={{ paddingTop: 12, fontSize: 12, color: '#9CA3AF' }} />}
        {series.map(s => (
          <Area
            key={s.name}
            type="monotone"
            dataKey={s.name}
            stroke={s.color}
            strokeWidth={2}
            fill={`url(#grad-${s.name})`}
            dot={false}
            activeDot={{ r: 4, fill: s.color, stroke: '#0A0F1C', strokeWidth: 2 }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}

// ── Revenue Bar Chart ──────────────────────────────────────────────────────────

interface BarDataPoint {
  name: string
  value: number
  color?: string
}

interface RevenueBarChartProps {
  data: BarDataPoint[]
  height?: number
  color?: string
}

export function RevenueBarChart({ data, height = 240, color = '#00D4FF' }: RevenueBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis
          tick={{ fill: '#6B7280', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => v >= 1000000 ? `$${(v/1000000).toFixed(1)}M` : v >= 1000 ? `$${(v/1000).toFixed(0)}K` : `$${v}`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color || color} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Donut / Pie Chart ─────────────────────────────────────────────────────────

interface DonutChartProps {
  data: BarDataPoint[]
  height?: number
}

export function DonutChart({ data, height = 220 }: DonutChartProps) {
  const COLORS = ['#00D4FF', '#7B3FE4', '#00C896', '#FFB800', '#FF4757', '#FF6B35', '#4ECDC4']
  const total = data.reduce((sum, d) => sum + d.value, 0)

  return (
    <div className="flex items-center gap-4">
      <ResponsiveContainer width={height} height={height}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={height * 0.3}
            outerRadius={height * 0.45}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex-1 space-y-2">
        {data.slice(0, 6).map((item, i) => (
          <div key={i} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
              <span className="text-xs text-gray-400 truncate">{item.name}</span>
            </div>
            <span className="text-xs font-semibold text-white flex-shrink-0">
              {((item.value / total) * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Simple Line Chart ──────────────────────────────────────────────────────────

interface SimpleLineChartProps {
  data: { date: string; value: number }[]
  color?: string
  height?: number
  label?: string
}

export function SimpleLineChart({ data, color = '#00D4FF', height = 180, label = 'value' }: SimpleLineChartProps) {
  const step = Math.max(1, Math.floor(data.length / 60))
  const sampled = data.filter((_, i) => i % step === 0)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={sampled} margin={{ top: 5, right: 10, left: 5, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
        <YAxis tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} name={label}
          activeDot={{ r: 4, fill: color, stroke: '#0A0F1C', strokeWidth: 2 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
