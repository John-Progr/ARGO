'use client'

import { useEffect, useRef, useState } from 'react'

const MAX_POINTS = 60

function Sparkline({ prices, isUp }: { prices: number[]; isUp: boolean }) {
  if (prices.length < 2) {
    return (
      <div className="h-12 w-full flex items-center">
        <div className="h-px w-full bg-zinc-300 dark:bg-zinc-700 animate-pulse rounded-full" />
      </div>
    )
  }

  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const W = 200
  const H = 48

  const pts = prices
    .map((p, i) => {
      const x = (i / (prices.length - 1)) * W
      const y = H - ((p - min) / range) * (H - 4) - 2
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  const lastY = H - ((prices.at(-1)! - min) / range) * (H - 4) - 2
  const stroke = isUp ? '#4ade80' : '#f87171'
  const fill = isUp ? 'rgba(74,222,128,0.08)' : 'rgba(248,113,113,0.08)'

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-12" preserveAspectRatio="none">
      <polygon points={`${pts} ${W},${H} 0,${H}`} fill={fill} />
      <polyline
        points={pts}
        fill="none"
        stroke={stroke}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={W} cy={lastY.toFixed(1)} r="2.5" fill={stroke} />
    </svg>
  )
}

function fmt(v: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(v)
}

export function BtcWidget() {
  const [history, setHistory] = useState<number[]>([])
  const [open24h, setOpen24h] = useState<number | null>(null)
  const [current, setCurrent] = useState<number | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let cancelled = false

    function connect() {
      if (cancelled) return
      const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@miniTicker')
      wsRef.current = ws

      ws.onopen = () => { if (!cancelled) setConnected(true) }

      ws.onmessage = (e) => {
        if (cancelled) return
        const msg = JSON.parse(e.data as string)
        const price = parseFloat(msg.c)
        const openPrice = parseFloat(msg.o)
        setCurrent(price)
        setOpen24h(openPrice)
        setHistory(prev => [...prev.slice(-(MAX_POINTS - 1)), price])
      }

      ws.onclose = () => {
        if (cancelled) return
        setConnected(false)
        setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()
    return () => {
      cancelled = true
      wsRef.current?.close()
    }
  }, [])

  const pct = current !== null && open24h !== null
    ? ((current - open24h) / open24h) * 100
    : null
  const isUp = pct === null ? true : pct >= 0

  return (
    <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-2xl p-4 flex flex-col gap-3 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
              alt="BTC"
              width={18}
              height={18}
              className="rounded-full"
            />
            <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">BTC / USD</span>
            <span className={`h-1.5 w-1.5 rounded-full transition-colors ${connected ? 'bg-green-400 animate-pulse' : 'bg-zinc-400'}`} />
          </div>
          <span className="text-2xl font-mono font-bold text-zinc-900 dark:text-white leading-none mt-0.5">
            {current !== null
              ? fmt(current)
              : <span className="text-sm text-zinc-400 dark:text-zinc-600 animate-pulse">Connecting…</span>}
          </span>
        </div>

        {pct !== null ? (
          <div className={`flex items-center gap-1 text-sm font-mono font-semibold px-2 py-1 rounded-lg ${
            isUp
              ? 'text-green-600 bg-green-500/10 dark:text-green-400 dark:bg-green-400/10'
              : 'text-red-600 bg-red-500/10 dark:text-red-400 dark:bg-red-400/10'
          }`}>
            <span>{isUp ? '▲' : '▼'}</span>
            <span>{Math.abs(pct).toFixed(2)}%</span>
          </div>
        ) : (
          <div className="text-xs font-mono text-zinc-300 dark:text-zinc-700 animate-pulse px-2 py-1">—%</div>
        )}
      </div>

      <Sparkline prices={history} isUp={isUp} />

      <span className="text-xs font-mono text-zinc-400 dark:text-zinc-600">
        24h change · Binance real-time
      </span>
    </div>
  )
}
