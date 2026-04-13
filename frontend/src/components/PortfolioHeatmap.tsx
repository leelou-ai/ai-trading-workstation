'use client'
import type { Position } from '@/lib/types'

interface Props { positions: Position[] }

export function PortfolioHeatmap({ positions }: Props) {
  if (!positions || positions.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#7d8590', fontSize: 12 }}>
        No positions yet
      </div>
    )
  }

  const totalVal = positions.reduce((s, p) => s + p.quantity * p.current_price, 0) || 1

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, height: '100%', alignContent: 'flex-start', overflow: 'hidden' }}>
      {positions.map(pos => {
        const weight = (pos.quantity * pos.current_price) / totalVal
        const pct = pos.unrealized_pnl_pct
        const intensity = Math.min(Math.abs(pct) / 10, 1)
        const alpha = 0.2 + intensity * 0.6
        const bg = pct >= 0
          ? `rgba(63, 185, 80, ${alpha})`
          : `rgba(248, 81, 73, ${alpha})`
        return (
          <div
            key={pos.ticker}
            style={{
              flex: `0 0 calc(${Math.max(weight * 100, 8)}% - 3px)`,
              minHeight: 50,
              backgroundColor: bg,
              borderRadius: 4,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 4,
              overflow: 'hidden',
            }}
          >
            <div style={{ color: '#e6edf3', fontWeight: 700, fontSize: 12, textAlign: 'center' }}>{pos.ticker}</div>
            <div style={{ color: pct >= 0 ? '#3fb950' : '#f85149', fontSize: 10 }}>
              {pct >= 0 ? '+' : ''}{pct.toFixed(1)}%
            </div>
          </div>
        )
      })}
    </div>
  )
}
