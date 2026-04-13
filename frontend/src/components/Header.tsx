'use client'
import type { Portfolio } from '@/lib/types'
import type { ConnectionStatus } from '@/hooks/usePriceStream'

const STATUS_COLOR: Record<ConnectionStatus, string> = {
  connected: '#3fb950',
  reconnecting: '#ecad0a',
  disconnected: '#f85149',
}

interface Props {
  portfolio: Portfolio | null
  status: ConnectionStatus
}

function fmt(n: number) {
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function Header({ portfolio, status }: Props) {
  const total = portfolio?.total_value ?? 0
  const cash = portfolio?.cash_balance ?? 0
  const pnl = portfolio?.total_pnl ?? 0

  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 16px', height: 48, backgroundColor: '#161b22',
      borderBottom: '1px solid #30363d', flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ color: '#ecad0a', fontWeight: 700, fontSize: 17, letterSpacing: 1 }}>FinAlly</span>
        <span style={{ color: '#30363d', fontSize: 12 }}>|</span>
        <span style={{ color: '#7d8590', fontSize: 11 }}>AI Trading Workstation</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 20, fontSize: 13 }}>
        <Stat label="Portfolio" value={`$${fmt(total)}`} />
        <Stat label="Cash" value={`$${fmt(cash)}`} />
        <Stat
          label="P&L"
          value={`${pnl >= 0 ? '+' : ''}$${fmt(pnl)}`}
          color={pnl >= 0 ? '#3fb950' : '#f85149'}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: STATUS_COLOR[status], boxShadow: `0 0 6px ${STATUS_COLOR[status]}` }} />
          <span style={{ color: '#7d8590', fontSize: 11 }}>{status}</span>
        </div>
      </div>
    </header>
  )
}

function Stat({ label, value, color = '#e6edf3' }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <span style={{ color: '#7d8590', fontSize: 11 }}>{label} </span>
      <span style={{ color, fontWeight: 600 }}>{value}</span>
    </div>
  )
}
