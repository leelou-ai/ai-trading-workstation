'use client'
import { useEffect, useRef, useState } from 'react'
import type { PriceUpdate, WatchlistItem } from '@/lib/types'
import { addToWatchlist, removeFromWatchlist } from '@/lib/api'

function Sparkline({ data }: { data: number[] }) {
  if (data.length < 2) return <svg width={64} height={28} />
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const w = 64, h = 28
  const pts = data.map((v, i) =>
    `${(i / (data.length - 1)) * w},${h - 2 - ((v - min) / range) * (h - 4)}`
  ).join(' ')
  const isUp = data[data.length - 1] >= data[0]
  return (
    <svg width={w} height={h} style={{ flexShrink: 0 }}>
      <polyline fill="none" stroke={isUp ? '#3fb950' : '#f85149'} strokeWidth="1.5" points={pts} />
    </svg>
  )
}

interface Props {
  watchlist: WatchlistItem[]
  prices: Record<string, PriceUpdate>
  selectedTicker: string | null
  onSelectTicker: (ticker: string) => void
  onWatchlistChange: () => void
}

export function WatchlistPanel({ watchlist, prices, selectedTicker, onSelectTicker, onWatchlistChange }: Props) {
  const [newTicker, setNewTicker] = useState('')
  const [error, setError] = useState('')
  const historyRef = useRef<Record<string, number[]>>({})
  const prevPricesRef = useRef<Record<string, number>>({})
  const flashRef = useRef<Record<string, string>>({})
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let changed = false
    for (const [ticker, update] of Object.entries(prices)) {
      const hist = historyRef.current[ticker] ?? []
      hist.push(update.price)
      if (hist.length > 60) hist.shift()
      historyRef.current[ticker] = hist

      const prev = prevPricesRef.current[ticker]
      if (prev !== undefined && prev !== update.price) {
        const cls = update.price > prev ? 'flash-green' : 'flash-red'
        flashRef.current[ticker] = cls
        changed = true
        setTimeout(() => {
          delete flashRef.current[ticker]
          setTick(n => n + 1)
        }, 600)
      }
      prevPricesRef.current[ticker] = update.price
    }
    if (changed) setTick(n => n + 1)
  }, [prices])

  const handleAdd = async () => {
    const t = newTicker.trim().toUpperCase()
    if (!t || !/^[A-Z]{1,10}$/.test(t)) {
      setError('Invalid ticker')
      return
    }
    try {
      await addToWatchlist(t)
      setNewTicker('')
      setError('')
      onWatchlistChange()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed')
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '6px 12px', borderBottom: '1px solid #30363d', color: '#7d8590', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, flexShrink: 0 }}>
        Watchlist
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {watchlist.map(item => {
          const live = prices[item.ticker]
          const price = live?.price ?? item.price
          const pct = live?.change_percent ?? item.change_percent
          const dir = live?.direction ?? item.direction
          const history = historyRef.current[item.ticker] ?? []
          const flashCls = flashRef.current[item.ticker] ?? ''
          const isSelected = selectedTicker === item.ticker

          return (
            <div
              key={item.ticker}
              className={flashCls}
              onClick={() => onSelectTicker(item.ticker)}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '5px 8px 5px 12px', cursor: 'pointer',
                backgroundColor: isSelected ? '#1a1a2e' : 'transparent',
                borderLeft: isSelected ? '2px solid #209dd7' : '2px solid transparent',
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ color: '#e6edf3', fontWeight: 600, fontSize: 13 }}>{item.ticker}</div>
                <div style={{ fontSize: 11, display: 'flex', gap: 6 }}>
                  <span style={{ color: '#e6edf3' }}>{price != null ? `$${price.toFixed(2)}` : '—'}</span>
                  {pct != null && (
                    <span style={{ color: dir === 'up' ? '#3fb950' : dir === 'down' ? '#f85149' : '#7d8590' }}>
                      {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>
              <Sparkline data={history} />
              <button
                onClick={e => { e.stopPropagation(); removeFromWatchlist(item.ticker).then(onWatchlistChange).catch(() => {}) }}
                style={{ background: 'none', border: 'none', color: '#7d8590', cursor: 'pointer', fontSize: 16, padding: '0 2px', lineHeight: 1, flexShrink: 0 }}
              >×</button>
            </div>
          )
        })}
      </div>
      <div style={{ padding: 8, borderTop: '1px solid #30363d', flexShrink: 0 }}>
        {error && <div style={{ color: '#f85149', fontSize: 11, marginBottom: 4 }}>{error}</div>}
        <div style={{ display: 'flex', gap: 4 }}>
          <input
            value={newTicker}
            onChange={e => setNewTicker(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            placeholder="ADD TICKER"
            maxLength={10}
            style={{ flex: 1, backgroundColor: '#0d1117', border: '1px solid #30363d', color: '#e6edf3', padding: '4px 8px', fontSize: 12, borderRadius: 4, outline: 'none', minWidth: 0 }}
          />
          <button
            onClick={handleAdd}
            style={{ backgroundColor: '#209dd7', border: 'none', color: '#fff', padding: '4px 10px', borderRadius: 4, cursor: 'pointer', fontSize: 13, fontWeight: 700, flexShrink: 0 }}
          >+</button>
        </div>
      </div>
    </div>
  )
}
