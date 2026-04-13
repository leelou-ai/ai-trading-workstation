'use client'
import { useEffect, useRef, useState } from 'react'
import type { PriceUpdate } from '@/lib/types'

export type ConnectionStatus = 'connected' | 'reconnecting' | 'disconnected'

export function usePriceStream() {
  const [prices, setPrices] = useState<Record<string, PriceUpdate>>({})
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')
  const esRef = useRef<EventSource | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    function connect() {
      if (esRef.current) {
        esRef.current.close()
        esRef.current = null
      }
      const es = new EventSource('/api/stream/prices')
      esRef.current = es

      es.onopen = () => setStatus('connected')

      es.onmessage = (event) => {
        try {
          // Backend sends a batch: { "AAPL": PriceUpdate, "GOOGL": PriceUpdate, ... }
          const batch: Record<string, PriceUpdate> = JSON.parse(event.data)
          setPrices(prev => ({ ...prev, ...batch }))
        } catch {
          // ignore malformed events
        }
      }

      es.onerror = () => {
        setStatus('reconnecting')
        es.close()
        esRef.current = null
        reconnectTimer.current = setTimeout(connect, 3000)
      }
    }

    connect()

    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      if (esRef.current) esRef.current.close()
    }
  }, [])

  return { prices, status }
}
