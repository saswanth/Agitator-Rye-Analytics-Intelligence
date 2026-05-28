import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, MessageSquare, Search, TrendingUp,
  Settings, Cpu, Lightbulb, ChevronRight, Zap, Activity
} from 'lucide-react'

const navItems = [
  { to: '/', label: 'Executive Dashboard', icon: LayoutDashboard, color: '#00D4FF' },
  { to: '/bi', label: 'Conversational BI', icon: MessageSquare, color: '#7B3FE4' },
  { to: '/rca', label: 'Root Cause Analysis', icon: Search, color: '#FF4757' },
  { to: '/financial', label: 'Financial Analysis', icon: TrendingUp, color: '#00C896' },
  { to: '/pipeline', label: 'Data Pipeline', icon: Cpu, color: '#FFB800' },
  { to: '/insights', label: 'Auto Insights', icon: Lightbulb, color: '#FF6B35' },
]

export default function Sidebar() {
  return (
    <aside className="w-64 flex-shrink-0 flex flex-col h-full border-r border-white/5 bg-navy-800/60 backdrop-blur-xl">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-glow to-purple-glow flex items-center justify-center shadow-lg glow-cyan">
            <Zap size={18} className="text-black" />
          </div>
          <div>
            <h1 className="text-white font-bold text-sm leading-tight">Agitator Rye</h1>
            <p className="text-gray-500 text-xs">Analytics Intelligence</p>
          </div>
        </div>
      </div>

      {/* Status indicator */}
      <div className="mx-4 mt-3 px-3 py-2 rounded-lg bg-emerald-glow/5 border border-emerald-glow/20 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-glow animate-pulse" />
        <span className="text-xs text-emerald-glow font-medium">5 Agents Active</span>
        <Activity size={12} className="ml-auto text-emerald-glow" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-widest">
          Modules
        </p>
        {navItems.map(({ to, label, icon: Icon, color }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `sidebar-item group ${isActive ? 'active' : ''}`
            }
            style={({ isActive }) => isActive ? { color } : {}}
          >
            <Icon size={16} style={{ color: 'inherit' }} />
            <span className="flex-1 text-sm">{label}</span>
            <ChevronRight size={12} className="opacity-0 group-hover:opacity-50 transition-opacity" />
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-white/5">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-glow to-cyan-glow flex items-center justify-center">
            <span className="text-xs font-bold text-white">AR</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-200 truncate">Agitator Rye</p>
            <p className="text-xs text-gray-500">v1.0.0 · Sarvam AI</p>
          </div>
          <Settings size={14} className="text-gray-600 hover:text-gray-300 cursor-pointer transition-colors" />
        </div>
      </div>
    </aside>
  )
}
