import { useEffect, useRef, useCallback, useState } from 'react'
import { createChatWebSocket } from '../services/api'

export type WSMessage =
  | { type: 'start'; agent: string; session_id: string }
  | { type: 'token'; content: string }
  | { type: 'done'; data: Record<string, unknown>; session_id: string }
  | { type: 'error'; message: string }

interface UseWebSocketOptions {
  sessionId: string
  onMessage: (msg: WSMessage) => void
  onError?: (error: Event) => void
}

export function useWebSocket({ sessionId, onMessage, onError }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [reconnecting, setReconnecting] = useState(false)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = createChatWebSocket(sessionId)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setReconnecting(false)
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage
        onMessage(msg)
      } catch {
        // ignore parse errors
      }
    }

    ws.onerror = (event) => {
      setConnected(false)
      onError?.(event)
    }

    ws.onclose = () => {
      setConnected(false)
      // Auto-reconnect after 3 seconds
      setReconnecting(true)
      setTimeout(() => {
        setReconnecting(false)
        connect()
      }, 3000)
    }
  }, [sessionId, onMessage, onError])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((payload: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload))
      return true
    }
    return false
  }, [])

  return { connected, reconnecting, send }
}
