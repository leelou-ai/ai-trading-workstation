'use client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import type { Snapshot } from '@/lib/types'

interface Props { snapshots: Snapshot[] }

export function PnLChart({ snapshots }: Props) {
  if (!snapshots || snapshots.length < 2) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#7d8590', fontSize: 12 }}>
        Accumulating data…
      </div>
    )
  }
  const data = snapshots.map(s => ({
    time: new Date(s.recorded_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    value: s.total_value,
  }))
  const first = data[0].value
  const last = data[data.length - 1].value
  const color = last >= first ? '#3fb950' : '#f85149'

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
        <XAxis dataKey="time" tick={{ fill: '#7d8590', fontSize: 9 }} interval="preserveStartEnd" axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#7d8590', fontSize: 9 }} tickFormatter={v => `$${(v / 1000).toFixed(1)}k`} axisLine={false} tickLine={false} width={40} />
        <Tooltip
          contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d', color: '#e6edf3', fontSize: 12 }}
          formatter={(v: number) => [`$${v.toFixed(2)}`, 'Value']}
        />
        <Line type="monotone" dataKey="value" stroke={color} dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  )
}
