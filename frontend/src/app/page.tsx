'use client'
import { useEffect, useState } from 'react'
import { Header } from '@/components/Header'
import { WatchlistPanel } from '@/components/WatchlistPanel'
import { MainChart } from '@/components/MainChart'
import { PortfolioHeatmap } from '@/components/PortfolioHeatmap'
import { PnLChart } from '@/components/PnLChart'
import { PositionsTable } from '@/components/PositionsTable'
import { TradeBar } from '@/components/TradeBar'
import { ChatPanel } from '@/components/ChatPanel'
import { usePriceStream } from '@/hooks/usePriceStream'
import { usePortfolio } from '@/hooks/usePortfolio'

export default function TradingTerminal() {
  const { prices, status } = usePriceStream()
  const { portfolio, watchlist, snapshots, refetch } = usePortfolio()
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedTicker && watchlist.length > 0) {
      setSelectedTicker(watchlist[0].ticker)
    }
  }, [watchlist, selectedTicker])

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'hidden',
      backgroundColor: '#0d1117',
      color: '#e6edf3',
      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    }}>
      <Header portfolio={portfolio} status={status} />

      {/* 3-column layout */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', minHeight: 0 }}>

        {/* LEFT: Watchlist */}
        <div style={{ width: 260, flexShrink: 0, borderRight: '1px solid #30363d', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <WatchlistPanel
            watchlist={watchlist}
            prices={prices}
            selectedTicker={selectedTicker}
            onSelectTicker={setSelectedTicker}
            onWatchlistChange={refetch}
          />
        </div>

        {/* CENTER: Charts + Positions + Trade Bar */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>

          {/* Main chart */}
          <div style={{ height: '38%', flexShrink: 0, borderBottom: '1px solid #30363d', backgroundColor: '#161b22', overflow: 'hidden' }}>
            <MainChart ticker={selectedTicker} prices={prices} />
          </div>

          {/* Heatmap + P&L */}
          <div style={{ height: '28%', flexShrink: 0, borderBottom: '1px solid #30363d', display: 'flex' }}>
            <div style={{ flex: 1, borderRight: '1px solid #30363d', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ color: '#7d8590', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, padding: '5px 10px', flexShrink: 0 }}>Heatmap</div>
              <div style={{ flex: 1, padding: '0 8px 8px', overflow: 'hidden' }}>
                <PortfolioHeatmap positions={portfolio?.positions ?? []} />
              </div>
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ color: '#7d8590', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, padding: '5px 10px', flexShrink: 0 }}>P&L Chart</div>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <PnLChart snapshots={snapshots} />
              </div>
            </div>
          </div>

          {/* Positions table */}
          <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
            <div style={{ color: '#7d8590', fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, padding: '5px 12px', borderBottom: '1px solid #30363d', position: 'sticky', top: 0, backgroundColor: '#0d1117' }}>
              Positions
            </div>
            <PositionsTable positions={portfolio?.positions ?? []} />
          </div>

          {/* Trade bar */}
          <TradeBar selectedTicker={selectedTicker} onTradeComplete={refetch} />
        </div>

        {/* RIGHT: Chat */}
        <div style={{ width: 300, flexShrink: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <ChatPanel />
        </div>
      </div>
    </div>
  )
}
