'use client'
import { useEffect, useRef, useState } from 'react'
import type { PriceUpdate } from '@/lib/types'

interface PricePoint { price: number; t: number }

interface Props {
  ticker: string | null
  prices: Record<string, PriceUpdate>
}

export function MainChart({ ticker, prices }: Props) {
  const historyRef = useRef<Record<string, PricePoint[]>>({})
  const [, setTick] = useState(0)

  useEffect(() => {
    if (!ticker) return
    const update = prices[ticker]
    if (!update) return
    const hist = historyRef.current[ticker] ?? []
    hist.push({ price: update.price, t: Date.now() })
    if (hist.length > 300) hist.shift()
    historyRef.current[ticker] = hist
    setTick(n => n + 1)
  }, [ticker, prices])

  if (!ticker) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#7d8590', fontSize: 14 }}>
        Select a ticker to view chart
      </div>
    )
  }

  const live = prices[ticker]
  const history = historyRef.current[ticker] ?? []

  return (
    <div style={{ padding: '12px 16px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8, flexShrink: 0 }}>
        <span style={{ color: '#e6edf3', fontWeight: 700, fontSize: 20 }}>{ticker}</span>
        {live && (
          <>
            <span style={{ color: '#e6edf3', fontSize: 18 }}>${live.price.toFixed(2)}</span>
            <span style={{ color: live.direction === 'up' ? '#3fb950' : live.direction === 'down' ? '#f85149' : '#7d8590', fontSize: 13 }}>
              {live.change >= 0 ? '+' : ''}{live.change.toFixed(2)} ({live.change_percent.toFixed(2)}%)
            </span>
          </>
        )}
      </div>
      <div style={{ flex: 1, backgroundColor: '#0d1117', borderRadius: 4, overflow: 'hidden', minHeight: 0 }}>
        {history.length >= 2 ? <PriceChart history={history} /> : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#7d8590', fontSize: 12 }}>
            Waiting for price data…
          </div>
        )}
      </div>
    </div>
  )
}

function PriceChart({ history }: { history: PricePoint[] }) {
  const W = 800, H = 160
  const prices = history.map(p => p.price)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const pad = { t: 8, b: 8, l: 8, r: 8 }
  const cw = W - pad.l - pad.r
  const ch = H - pad.t - pad.b

  const toX = (i: number) => pad.l + (i / (history.length - 1)) * cw
  const toY = (p: number) => pad.t + ch - ((p - min) / range) * ch

  const pts = history.map((p, i) => `${toX(i)},${toY(p.price)}`).join(' ')
  const isUp = prices[prices.length - 1] >= prices[0]
  const color = isUp ? '#3fb950' : '#f85149'
  const fillId = 'grad'

  // Area fill path
  const first = { x: toX(0), y: toY(history[0].price) }
  const last = { x: toX(history.length - 1), y: toY(history[history.length - 1].price) }
  const areaPath = `M${first.x},${pad.t + ch} L${pts.split(' ').map(p => p).join(' L')} L${last.x},${pad.t + ch} Z`

  return (
    <svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${fillId})`} />
      <polyline fill="none" stroke={color} strokeWidth="1.5" points={pts} />
    </svg>
  )
}
