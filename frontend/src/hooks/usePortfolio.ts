'use client'
import { useCallback, useEffect, useState } from 'react'
import { getPortfolio, getWatchlist, getPortfolioHistory } from '@/lib/api'
import type { Portfolio, WatchlistItem, Snapshot } from '@/lib/types'

export function usePortfolio() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])

  const refetch = useCallback(async () => {
    try {
      const [p, w, h] = await Promise.all([
        getPortfolio(),
        getWatchlist(),
        getPortfolioHistory(),
      ])
      setPortfolio(p)
      setWatchlist(w.tickers ?? [])
      setSnapshots(h.snapshots ?? [])
    } catch {
      // silently retry on next interval
    }
  }, [])

  useEffect(() => {
    refetch()
    const id = setInterval(refetch, 10_000)
    return () => clearInterval(id)
  }, [refetch])

  return { portfolio, watchlist, snapshots, refetch }
}
