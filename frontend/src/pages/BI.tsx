import ChatInterface from '../components/Chat/ChatInterface'
import { Database, Zap, Table, BarChart2, Code } from 'lucide-react'

const SUGGESTED = [
  "What were the top 5 products by revenue last quarter?",
  "Show me month-over-month revenue growth by region",
  "Which customer segment has the highest average order value?",
  "What is our conversion rate trend over the last 90 days?",
]

const CAPABILITIES = [
  { icon: Database, label: 'SQL Generation', desc: 'Converts questions to optimised SQL' },
  { icon: Zap, label: 'Self-Healing', desc: 'Auto-corrects SQL errors up to 3 times' },
  { icon: BarChart2, label: 'Auto Charts', desc: 'Picks the best chart type for your data' },
  { icon: Table, label: 'Table View', desc: 'Inspect raw query results in a table' },
  { icon: Code, label: 'SQL View', desc: 'View the exact SQL query executed' },
]

export default function BI() {
  return (
    <div className="flex gap-6 h-[calc(100vh-128px)]">
      {/* Chat Panel */}
      <div className="flex-1 glass-card overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-glow/20 to-cyan-glow/20 border border-purple-glow/30 flex items-center justify-center">
            <Database size={15} className="text-purple-glow" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-sm">Text-to-SQL Agent</h3>
            <p className="text-gray-500 text-xs">Querying 150K+ sales transactions</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-glow animate-pulse" />
            <span className="text-xs text-emerald-glow">Active</span>
          </div>
        </div>
        <ChatInterface
          agent="bi"
          placeholder="Ask about your business data..."
          suggestedQueries={SUGGESTED}
        />
      </div>

      {/* Capabilities Panel */}
      <div className="w-64 space-y-4">
        <div className="glass-card p-5">
          <h4 className="text-white font-semibold text-sm mb-4">Agent Capabilities</h4>
          <div className="space-y-3">
            {CAPABILITIES.map(({ icon: Icon, label, desc }) => (
              <div key={label} className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/5 flex items-center justify-center flex-shrink-0">
                  <Icon size={14} className="text-cyan-glow" />
                </div>
                <div>
                  <p className="text-white text-xs font-medium">{label}</p>
                  <p className="text-gray-500 text-xs mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-5">
          <h4 className="text-white font-semibold text-sm mb-3">Available Tables</h4>
          <div className="space-y-1.5">
            {[
              { name: 'sales_transactions', rows: '150K' },
              { name: 'customers', rows: '15K' },
              { name: 'products', rows: '500' },
              { name: 'daily_metrics', rows: '1,825' },
              { name: 'financial_data', rows: '60mo' },
              { name: 'web_analytics', rows: '1,825' },
            ].map(t => (
              <div key={t.name} className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-white/3 transition-colors">
                <span className="text-gray-400 text-xs font-mono">{t.name}</span>
                <span className="text-gray-600 text-xs">{t.rows}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
