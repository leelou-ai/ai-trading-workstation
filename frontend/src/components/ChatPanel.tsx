'use client'
import { useEffect, useRef, useState } from 'react'
import { sendChatMessage } from '@/lib/api'
import type { ChatMessage } from '@/lib/types'

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const data = await sendChatMessage(text)
      const trades = data.executed_trades ?? []
      const changes = data.executed_watchlist_changes ?? []
      const actions = trades.length || changes.length
        ? { executed_trades: trades, executed_watchlist_changes: changes }
        : undefined
      setMessages(prev => [...prev, { role: 'assistant', content: data.message, actions }])
    } catch (e: unknown) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${e instanceof Error ? e.message : 'Request failed'}`,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', borderLeft: '1px solid #30363d' }}>
      <div style={{ padding: '6px 12px', borderBottom: '1px solid #30363d', color: '#7d8590', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, flexShrink: 0 }}>
        AI Assistant
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '10px 10px 0', display: 'flex', flexDirection: 'column', gap: 8, minHeight: 0 }}>
        {messages.length === 0 && (
          <div style={{ color: '#7d8590', fontSize: 12, textAlign: 'center', marginTop: 20 }}>
            Ask me about your portfolio,<br />market analysis, or to place trades.
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i}>
            <div style={{
              maxWidth: '90%',
              marginLeft: msg.role === 'user' ? 'auto' : 0,
              padding: '7px 10px',
              borderRadius: 6,
              fontSize: 13,
              backgroundColor: msg.role === 'user' ? '#1a1a2e' : '#161b22',
              border: '1px solid #30363d',
              color: '#e6edf3',
              lineHeight: 1.5,
            }}>
              <div style={{ color: '#7d8590', fontSize: 10, marginBottom: 3 }}>
                {msg.role === 'user' ? 'You' : '✦ FinAlly'}
              </div>
              {msg.content}
            </div>
            {msg.actions?.executed_trades?.map((t, j) => (
              <div key={j} style={{ fontSize: 11, color: t.success ? '#3fb950' : '#f85149', marginTop: 2, paddingLeft: 4 }}>
                {t.success ? '✓' : '✗'} {t.side?.toUpperCase()} {t.quantity} {t.ticker}
                {t.price ? ` @ $${t.price.toFixed(2)}` : ''}{t.error ? `: ${t.error}` : ''}
              </div>
            ))}
            {msg.actions?.executed_watchlist_changes?.map((c, j) => (
              <div key={j} style={{ fontSize: 11, color: c.success ? '#3fb950' : '#f85149', marginTop: 2, paddingLeft: 4 }}>
                {c.success ? '✓' : '✗'} Watchlist: {c.action} {c.ticker}
              </div>
            ))}
          </div>
        ))}
        {loading && (
          <div style={{ color: '#7d8590', fontSize: 12, fontStyle: 'italic' }}>FinAlly is thinking…</div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{ padding: 8, borderTop: '1px solid #30363d', display: 'flex', gap: 6, flexShrink: 0 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask FinAlly…"
          style={{ flex: 1, backgroundColor: '#0d1117', border: '1px solid #30363d', color: '#e6edf3', padding: '6px 10px', fontSize: 13, borderRadius: 4, outline: 'none', minWidth: 0 }}
        />
        <button
          onClick={send}
          disabled={loading}
          style={{ backgroundColor: '#753991', border: 'none', color: '#fff', padding: '6px 12px', borderRadius: 4, cursor: 'pointer', fontSize: 13, flexShrink: 0 }}
        >Send</button>
      </div>
    </div>
  )
}
