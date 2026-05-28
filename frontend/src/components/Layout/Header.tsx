import { Bell, RefreshCw, Search, Wifi, WifiOff } from 'lucide-react'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '../../services/api'

interface HeaderProps {
  title: string
  subtitle?: string
}

export default function Header({ title, subtitle }: HeaderProps) {
  const [searchOpen, setSearchOpen] = useState(false)

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  })

  const isOnline = health?.status === 'healthy'

  return (
    <header className="h-16 flex-shrink-0 flex items-center justify-between px-6 border-b border-white/5 bg-navy-800/40 backdrop-blur-xl">
      {/* Left: Title */}
      <div>
        <h2 className="text-white font-semibold text-lg leading-tight">{title}</h2>
        {subtitle && <p className="text-gray-500 text-xs">{subtitle}</p>}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <button
          onClick={() => setSearchOpen(!searchOpen)}
          className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center transition-all border border-white/5"
        >
          <Search size={15} className="text-gray-400" />
        </button>

        {/* Refresh */}
        <button className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center transition-all border border-white/5">
          <RefreshCw size={15} className="text-gray-400" />
        </button>

        {/* Notifications */}
        <div className="relative">
          <button className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center transition-all border border-white/5">
            <Bell size={15} className="text-gray-400" />
          </button>
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-glow text-white text-[10px] font-bold flex items-center justify-center">
            3
          </span>
        </div>

        {/* Connection status */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-medium ${
            isOnline
              ? 'bg-emerald-glow/10 border-emerald-glow/20 text-emerald-glow'
              : 'bg-red-glow/10 border-red-glow/20 text-red-glow'
          }`}
        >
          {isOnline ? <Wifi size={12} /> : <WifiOff size={12} />}
          {isOnline ? 'Connected' : 'Offline'}
        </div>

        {/* Last updated */}
        <span className="text-xs text-gray-600">
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </header>
  )
}
