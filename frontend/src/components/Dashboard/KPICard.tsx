import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface KPICardProps {
  title: string
  value: string
  delta: number
  deltaLabel: string
  trend: 'up' | 'down' | 'neutral'
  icon: string
  gradient?: string
  delay?: number
}

const GRADIENTS: Record<string, string> = {
  'dollar-sign': 'linear-gradient(135deg, #00D4FF, #0098FF)',
  'shopping-cart': 'linear-gradient(135deg, #7B3FE4, #9B59F9)',
  'target': 'linear-gradient(135deg, #00C896, #00D4FF)',
  'users': 'linear-gradient(135deg, #FFB800, #FF6B35)',
  'star': 'linear-gradient(135deg, #FF6B35, #FF4757)',
  'trending-up': 'linear-gradient(135deg, #9B59F9, #7B3FE4)',
}

const GLOW_COLORS: Record<string, string> = {
  'dollar-sign': 'rgba(0, 212, 255, 0.3)',
  'shopping-cart': 'rgba(123, 63, 228, 0.3)',
  'target': 'rgba(0, 200, 150, 0.3)',
  'users': 'rgba(255, 184, 0, 0.3)',
  'star': 'rgba(255, 107, 53, 0.3)',
  'trending-up': 'rgba(155, 89, 249, 0.3)',
}

export default function KPICard({ title, value, delta, deltaLabel, trend, icon, delay = 0 }: KPICardProps) {
  const gradient = GRADIENTS[icon] || GRADIENTS['dollar-sign']
  const glowColor = GLOW_COLORS[icon] || GLOW_COLORS['dollar-sign']

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendColor = trend === 'up' ? '#00C896' : trend === 'down' ? '#FF4757' : '#9CA3AF'
  const trendBg = trend === 'up' ? 'rgba(0,200,150,0.1)' : trend === 'down' ? 'rgba(255,71,87,0.1)' : 'rgba(156,163,175,0.1)'

  return (
    <motion.div
      className="kpi-card"
      style={{ '--kpi-gradient': gradient } as React.CSSProperties}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -4 }}
    >
      {/* Background glow */}
      <div
        className="absolute inset-0 rounded-2xl opacity-30 pointer-events-none"
        style={{ background: `radial-gradient(ellipse at top right, ${glowColor}, transparent 70%)` }}
      />

      <div className="relative z-10 flex items-start justify-between">
        <div className="flex-1">
          <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-2">{title}</p>
          <p className="text-white text-2xl font-bold tracking-tight">{value}</p>

          <div
            className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg"
            style={{ background: trendBg }}
          >
            <TrendIcon size={12} style={{ color: trendColor }} />
            <span className="text-xs font-semibold" style={{ color: trendColor }}>
              {delta > 0 ? '+' : ''}{delta.toFixed(1)}%
            </span>
            <span className="text-gray-600 text-xs">{deltaLabel}</span>
          </div>
        </div>

        {/* Icon */}
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ml-4"
          style={{ background: gradient, boxShadow: `0 4px 16px ${glowColor}` }}
        >
          <span className="text-xl">
            {icon === 'dollar-sign' && '💰'}
            {icon === 'shopping-cart' && '🛒'}
            {icon === 'target' && '🎯'}
            {icon === 'users' && '👥'}
            {icon === 'star' && '⭐'}
            {icon === 'trending-up' && '📈'}
          </span>
        </div>
      </div>
    </motion.div>
  )
}
