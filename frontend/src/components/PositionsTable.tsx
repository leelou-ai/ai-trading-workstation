'use client'
import type { Position } from '@/lib/types'

interface Props { positions: Position[] }

export function PositionsTable({ positions }: Props) {
  if (!positions || positions.length === 0) {
    return <div style={{ color: '#7d8590', fontSize: 12, padding: '12px 16px' }}>No open positions</div>
  }
  const sorted = [...positions].sort((a, b) => Math.abs(b.unrealized_pnl) - Math.abs(a.unrealized_pnl))
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
      <thead>
        <tr style={{ borderBottom: '1px solid #30363d' }}>
          {['Ticker', 'Qty', 'Avg Cost', 'Current', 'P&L', 'P&L %'].map(h => (
            <th key={h} style={{ textAlign: h === 'Ticker' ? 'left' : 'right', padding: '5px 12px', color: '#7d8590', fontWeight: 400, whiteSpace: 'nowrap' }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sorted.map(pos => (
          <tr key={pos.ticker} style={{ borderBottom: '1px solid #21262d' }}>
            <td style={{ padding: '4px 12px', color: '#209dd7', fontWeight: 600 }}>{pos.ticker}</td>
            <td style={{ padding: '4px 12px', textAlign: 'right', color: '#e6edf3' }}>{pos.quantity}</td>
            <td style={{ padding: '4px 12px', textAlign: 'right', color: '#e6edf3' }}>${pos.avg_cost.toFixed(2)}</td>
            <td style={{ padding: '4px 12px', textAlign: 'right', color: '#e6edf3' }}>${pos.current_price.toFixed(2)}</td>
            <td style={{ padding: '4px 12px', textAlign: 'right', color: pos.unrealized_pnl >= 0 ? '#3fb950' : '#f85149' }}>
              {pos.unrealized_pnl >= 0 ? '+' : ''}${Math.abs(pos.unrealized_pnl).toFixed(2)}
            </td>
            <td style={{ padding: '4px 12px', textAlign: 'right', color: pos.unrealized_pnl_pct >= 0 ? '#3fb950' : '#f85149' }}>
              {pos.unrealized_pnl_pct >= 0 ? '+' : ''}{pos.unrealized_pnl_pct.toFixed(2)}%
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
