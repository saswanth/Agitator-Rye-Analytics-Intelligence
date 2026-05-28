import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader2, Code, BarChart2, Table } from 'lucide-react'
import { useWebSocket } from '../../hooks/useWebSocket'
import { RevenueBarChart, SimpleLineChart } from '../Dashboard/Charts'

const genId = () => Math.random().toString(36).slice(2) + Date.now().toString(36)

interface Message {
  id: string
  role: 'user' | 'ai'
  content: string
  streaming?: boolean
  data?: Record<string, any>
  chartSpec?: any
  sqlQuery?: string
  tableData?: any[]
}

interface ChatInterfaceProps {
  agent?: string
  persona?: string
  placeholder?: string
  suggestedQueries?: string[]
}

export default function ChatInterface({
  agent = 'bi',
  persona = 'analyst',
  placeholder = 'Ask anything about your business data...',
  suggestedQueries = [],
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<Record<string, 'text' | 'chart' | 'sql' | 'table'>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const sessionId = useRef(genId())
  const currentMsgId = useRef<string | null>(null)

  const handleMessage = useCallback((msg: any) => {
    if (msg.type === 'start') {
      const id = genId()
      currentMsgId.current = id
      setMessages(prev => [...prev, { id, role: 'ai', content: '', streaming: true }])
    } else if (msg.type === 'token' && currentMsgId.current) {
      setMessages(prev =>
        prev.map(m =>
          m.id === currentMsgId.current
            ? { ...m, content: m.content + msg.content }
            : m
        )
      )
    } else if (msg.type === 'done' && currentMsgId.current) {
      const data = msg.data || {}
      setMessages(prev =>
        prev.map(m =>
          m.id === currentMsgId.current
            ? {
                ...m,
                streaming: false,
                content: m.content || (data.answer ?? data.summary ?? data.executive_summary ?? 'Analysis complete.'),
                data,
                chartSpec: data.chart_spec,
                sqlQuery: data.sql_query,
                tableData: data.rows,
              }
            : m
        )
      )
      currentMsgId.current = null
      setLoading(false)
    } else if (msg.type === 'error') {
      setMessages(prev => [
        ...prev,
        { id: genId(), role: 'ai', content: `Error: ${msg.message}` },
      ])
      setLoading(false)
    }
  }, [])

  const { connected, send } = useWebSocket({
    sessionId: sessionId.current,
    onMessage: handleMessage,
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || loading) return

    setMessages(prev => [...prev, { id: genId(), role: 'user', content: text }])
    setInput('')
    setLoading(true)

    const sent = send({ message: text, agent, persona })
    if (!sent) {
      // Fallback to REST if WS not connected
      import('../../services/api').then(({ runQuery }) => {
        runQuery(text).then(result => {
          const id = genId()
          setMessages(prev => [
            ...prev,
            {
              id,
              role: 'ai',
              content: result.answer || 'Analysis complete.',
              chartSpec: result.chart_spec,
              sqlQuery: result.sql_query,
              tableData: result.rows,
            },
          ])
          setLoading(false)
        }).catch(() => setLoading(false))
      })
    }
  }

  const setTab = (msgId: string, tab: 'text' | 'chart' | 'sql' | 'table') => {
    setActiveTab(prev => ({ ...prev, [msgId]: tab }))
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center py-12">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-glow/20 to-purple-glow/20 border border-cyan-glow/20 flex items-center justify-center">
              <Bot size={28} className="text-cyan-glow" />
            </div>
            <div>
              <h3 className="text-white font-semibold text-lg mb-2">Ask Agitator Rye</h3>
              <p className="text-gray-500 text-sm max-w-md">
                I can query your data, explain trends, and generate charts. Try one of the suggestions below.
              </p>
            </div>
            {suggestedQueries.length > 0 && (
              <div className="grid grid-cols-1 gap-2 w-full max-w-lg">
                {suggestedQueries.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(q)}
                    className="text-left px-4 py-3 rounded-xl bg-white/5 hover:bg-cyan-glow/10 border border-white/5 hover:border-cyan-glow/20 text-gray-300 text-sm transition-all"
                  >
                    "{q}"
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map(msg => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'ai' && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-glow/20 to-purple-glow/20 border border-cyan-glow/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <Bot size={14} className="text-cyan-glow" />
                </div>
              )}
              <div className="max-w-[85%] space-y-2">
                {msg.role === 'user' ? (
                  <div className="chat-bubble-user">{msg.content}</div>
                ) : (
                  <div>
                    {/* Tab bar for AI messages with rich data */}
                    {(msg.chartSpec || msg.sqlQuery || msg.tableData) && !msg.streaming && (
                      <div className="flex gap-1 mb-2">
                        {['text', ...(msg.chartSpec ? ['chart'] : []), ...(msg.sqlQuery ? ['sql'] : []), ...(msg.tableData ? ['table'] : [])].map(tab => (
                          <button
                            key={tab}
                            onClick={() => setTab(msg.id, tab as any)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                              (activeTab[msg.id] || 'text') === tab
                                ? 'bg-cyan-glow/15 text-cyan-glow border border-cyan-glow/30'
                                : 'bg-white/5 text-gray-400 hover:bg-white/10'
                            }`}
                          >
                            {tab === 'chart' && <BarChart2 size={12} />}
                            {tab === 'sql' && <Code size={12} />}
                            {tab === 'table' && <Table size={12} />}
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Content based on active tab */}
                    {(activeTab[msg.id] || 'text') === 'text' && (
                      <div className="chat-bubble-ai">
                        {msg.streaming && !msg.content && (
                          <div className="flex gap-1 py-1">
                            <span className="typing-dot w-2 h-2 rounded-full bg-cyan-glow" />
                            <span className="typing-dot w-2 h-2 rounded-full bg-cyan-glow" />
                            <span className="typing-dot w-2 h-2 rounded-full bg-cyan-glow" />
                          </div>
                        )}
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    )}

                    {activeTab[msg.id] === 'chart' && msg.chartSpec && (
                      <div className="glass-card p-4 rounded-xl border border-white/6">
                        <p className="text-xs text-gray-500 mb-3">{msg.chartSpec.title}</p>
                        {msg.chartSpec.data && (
                          <RevenueBarChart
                            data={msg.chartSpec.data.slice(0, 20).map((d: any, i: number) => ({
                              name: String(Object.values(d)[0] ?? i),
                              value: Number(Object.values(d)[1] ?? 0),
                            }))}
                            height={200}
                          />
                        )}
                      </div>
                    )}

                    {activeTab[msg.id] === 'sql' && msg.sqlQuery && (
                      <pre className="code-block text-xs whitespace-pre-wrap">{msg.sqlQuery}</pre>
                    )}

                    {activeTab[msg.id] === 'table' && msg.tableData && (
                      <div className="glass-card rounded-xl border border-white/6 overflow-auto max-h-48">
                        <table className="w-full text-xs">
                          <thead className="border-b border-white/5">
                            <tr>
                              {Object.keys(msg.tableData[0] || {}).map(k => (
                                <th key={k} className="text-left px-3 py-2 text-gray-500 font-medium">{k}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {msg.tableData.slice(0, 20).map((row, i) => (
                              <tr key={i} className="border-b border-white/3 hover:bg-white/2">
                                {Object.values(row).map((v, j) => (
                                  <td key={j} className="px-3 py-2 text-gray-300">{String(v)}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-glow to-cyan-glow flex items-center justify-center flex-shrink-0 mt-1">
                  <User size={14} className="text-white" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && !messages.some(m => m.streaming) && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-glow/20 to-purple-glow/20 flex items-center justify-center">
              <Loader2 size={14} className="text-cyan-glow animate-spin" />
            </div>
            <div className="chat-bubble-ai">
              <div className="flex gap-1">
                <span className="typing-dot w-2 h-2 rounded-full bg-cyan-glow" />
                <span className="typing-dot w-2 h-2 rounded-full bg-cyan-glow" />
                <span className="typing-dot w-2 h-2 rounded-full bg-cyan-glow" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-4 pb-4">
        {/* Connection status */}
        {!connected && (
          <div className="mb-2 px-3 py-1.5 rounded-lg bg-amber-glow/10 border border-amber-glow/20 text-amber-glow text-xs text-center">
            Reconnecting to server...
          </div>
        )}
        <div className="flex gap-2 glass-card p-2 rounded-2xl border border-white/8">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder={placeholder}
            rows={1}
            className="flex-1 bg-transparent text-gray-200 text-sm placeholder-gray-600 resize-none outline-none px-2 py-2 leading-relaxed"
            style={{ maxHeight: 120 }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-glow to-purple-glow flex items-center justify-center flex-shrink-0 self-end transition-all hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg"
          >
            {loading ? (
              <Loader2 size={16} className="text-black animate-spin" />
            ) : (
              <Send size={16} className="text-black" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-600 text-center mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
