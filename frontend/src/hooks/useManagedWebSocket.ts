import { useEffect, useRef, useState } from 'react'
import { createWebSocketUrl } from '../api/websocket'
import type { RealtimeConnectionState } from '../types'

type MessageEnvelope = { type?: string }

interface UseManagedWebSocketOptions<TMessage> {
  path: string
  enabled?: boolean
  heartbeatMs?: number
  baseReconnectMs?: number
  maxReconnectMs?: number
  onMessage: (message: TMessage) => void
}

export function useManagedWebSocket<TMessage>({
  path,
  enabled = true,
  heartbeatMs = 15000,
  baseReconnectMs = 1000,
  maxReconnectMs = 10000,
  onMessage,
}: UseManagedWebSocketOptions<TMessage>) {
  const onMessageRef = useRef(onMessage)
  const socketRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<number | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const reconnectAttemptRef = useRef(0)
  const manualCloseRef = useRef(false)

  const [connectionState, setConnectionState] = useState<RealtimeConnectionState>(
    enabled && path ? 'connecting' : 'offline'
  )
  const [retryAttempt, setRetryAttempt] = useState(0)
  const [lastMessageAt, setLastMessageAt] = useState<string | null>(null)

  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    if (!enabled || !path) {
      setConnectionState('offline')
      setRetryAttempt(0)
      setLastMessageAt(null)
      return
    }

    manualCloseRef.current = false
    reconnectAttemptRef.current = 0
    setConnectionState('connecting')
    setRetryAttempt(0)
    setLastMessageAt(null)

    const clearHeartbeat = () => {
      if (heartbeatRef.current !== null) {
        window.clearInterval(heartbeatRef.current)
        heartbeatRef.current = null
      }
    }

    const clearReconnectTimeout = () => {
      if (reconnectTimeoutRef.current !== null) {
        window.clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }

    const cleanupSocket = () => {
      if (!socketRef.current) {
        return
      }

      socketRef.current.onopen = null
      socketRef.current.onmessage = null
      socketRef.current.onerror = null
      socketRef.current.onclose = null
      socketRef.current.close()
      socketRef.current = null
    }

    const scheduleReconnect = () => {
      if (manualCloseRef.current) {
        return
      }

      const nextAttempt = reconnectAttemptRef.current + 1
      reconnectAttemptRef.current = nextAttempt
      setRetryAttempt(nextAttempt)
      setConnectionState('reconnecting')

      const jitterMs = Math.floor(Math.random() * 250)
      const delayMs =
        Math.min(baseReconnectMs * 2 ** (nextAttempt - 1), maxReconnectMs) + jitterMs

      clearReconnectTimeout()
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, delayMs)
    }

    const connect = () => {
      clearReconnectTimeout()
      cleanupSocket()

      setConnectionState(
        reconnectAttemptRef.current > 0 ? 'reconnecting' : 'connecting'
      )

      const socket = new WebSocket(createWebSocketUrl(path))
      socketRef.current = socket

      socket.onopen = () => {
        reconnectAttemptRef.current = 0
        setRetryAttempt(0)
        setConnectionState('live')

        clearHeartbeat()
        heartbeatRef.current = window.setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'ping' }))
          }
        }, heartbeatMs)
      }

      socket.onmessage = (event) => {
        let message: TMessage | MessageEnvelope

        try {
          message = JSON.parse(event.data) as TMessage | MessageEnvelope
        } catch {
          return
        }

        if ((message as MessageEnvelope).type === 'pong') {
          return
        }

        setConnectionState('live')
        setLastMessageAt(new Date().toISOString())
        onMessageRef.current(message as TMessage)
      }

      socket.onerror = () => {
        if (
          socket.readyState === WebSocket.CONNECTING ||
          socket.readyState === WebSocket.OPEN
        ) {
          socket.close()
        }
      }

      socket.onclose = (event) => {
        clearHeartbeat()
        socketRef.current = null

        if (manualCloseRef.current) {
          return
        }

        if (event.code === 1008) {
          setConnectionState('offline')
          return
        }

        scheduleReconnect()
      }
    }

    connect()

    return () => {
      manualCloseRef.current = true
      clearReconnectTimeout()
      clearHeartbeat()
      cleanupSocket()
    }
  }, [baseReconnectMs, enabled, heartbeatMs, maxReconnectMs, path])

  return { connectionState, retryAttempt, lastMessageAt }
}
