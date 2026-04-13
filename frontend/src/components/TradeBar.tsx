'use client'
import { useEffect, useState } from 'react'
import { executeTrade } from '@/lib/api'

interface Props {
  selectedTicker: string | null
  onTradeComplete: () => void
}

export function TradeBar({ selectedTicker, onTradeComplete }: Props) {
  const [ticker, setTicker] = useState('')
  const [quantity, setQuantity] = useState('')
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (selectedTicker) setTicker(selectedTicker)
  }, [selectedTicker])

  const trade = async (side: 'buy' | 'sell') => {
    const t = ticker.trim().toUpperCase()
    const q = parseFloat(quantity)
    if (!t || isNaN(q) || q <= 0) {
      setMsg({ text: 'Enter ticker and quantity', ok: false })
      return
    }
    setLoading(true)
    try {
      await executeTrade(t, side, q)
      setMsg({ text: `${side.toUpperCase()} ${q} ${t} ✓`, ok: true })
      onTradeComplete()
      setTimeout(() => setMsg(null), 3000)
    } catch (e: unknown) {
      setMsg({ text: e instanceof Error ? e.message : 'Failed', ok: false })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', backgroundColor: '#161b22', borderTop: '1px solid #30363d', flexShrink: 0 }}>
      <span style={{ color: '#7d8590', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1 }}>Trade</span>
      <input
        value={ticker}
        onChange={e => setTicker(e.target.value.toUpperCase())}
        placeholder="TICKER"
        maxLength={10}
        style={{ width: 85, backgroundColor: '#0d1117', border: '1px solid #30363d', color: '#e6edf3', padding: '4px 8px', fontSize: 13, borderRadius: 4, outline: 'none' }}
      />
      <input
        value={quantity}
        onChange={e => setQuantity(e.target.value)}
        placeholder="QTY"
        type="number"
        min="0.01"
        step="any"
        style={{ width: 75, backgroundColor: '#0d1117', border: '1px solid #30363d', color: '#e6edf3', padding: '4px 8px', fontSize: 13, borderRadius: 4, outline: 'none' }}
      />
      <button
        onClick={() => trade('buy')}
        disabled={loading}
        style={{ backgroundColor: '#3fb950', border: 'none', color: '#0d1117', padding: '4px 16px', borderRadius: 4, cursor: 'pointer', fontWeight: 700, fontSize: 13 }}
      >BUY</button>
      <button
        onClick={() => trade('sell')}
        disabled={loading}
        style={{ backgroundColor: '#f85149', border: 'none', color: '#fff', padding: '4px 14px', borderRadius: 4, cursor: 'pointer', fontWeight: 700, fontSize: 13 }}
      >SELL</button>
      {msg && (
        <span style={{ fontSize: 12, color: msg.ok ? '#3fb950' : '#f85149', marginLeft: 4 }}>{msg.text}</span>
      )}
    </div>
  )
}
