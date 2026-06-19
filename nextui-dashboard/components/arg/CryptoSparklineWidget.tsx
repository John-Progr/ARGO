import { useEffect, useRef, useState } from 'react'

// ── constants ──────────────────────────────────────────────────────────────
const BUCKET_MS   = 15 * 60 * 1000   // 15m — smallest round interval Binance supports above 5m
const MAX_HISTORY = 72
const MAX_TICKS   = 300  // fallback: accumulate raw ticks when klines fails

function bucket() { return Math.floor(Date.now() / BUCKET_MS) }

// ── smooth bezier path ─────────────────────────────────────────────────────
function smoothPath(
  prices: number[],
  xFn: (i: number) => number,
  yFn: (p: number) => number,
): string {
  if (prices.length < 2) return ''
  let d = `M ${xFn(0).toFixed(2)} ${yFn(prices[0]!).toFixed(2)}`
  for (let i = 1; i < prices.length; i++) {
    const x0 = xFn(i - 1), y0 = yFn(prices[i - 1]!)
    const x1 = xFn(i),     y1 = yFn(prices[i]!)
    const cpx = (x0 + x1) / 2
    d += ` C ${cpx.toFixed(2)} ${y0.toFixed(2)} ${cpx.toFixed(2)} ${y1.toFixed(2)} ${x1.toFixed(2)} ${y1.toFixed(2)}`
  }
  return d
}

// ── chart ──────────────────────────────────────────────────────────────────
function AreaChart({ prices, isUp }: { prices: number[]; isUp: boolean }) {
  if (prices.length < 2) {
    return (
      <div className="w-full h-36 rounded-xl flex items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-2 border-zinc-600 border-t-zinc-400 rounded-full animate-spin" />
          <span className="text-xs font-mono text-zinc-600">Fetching chart data…</span>
        </div>
      </div>
    )
  }

  const W = 600
  const H = 140
  const PX = 4
  const PY = 8

  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || max * 0.01

  const xFn = (i: number) => PX + (i / (prices.length - 1)) * (W - PX * 2)
  const yFn = (p: number) => PY + (1 - (p - min) / range) * (H - PY * 2)

  const linePath = smoothPath(prices, xFn, yFn)
  const lastX    = xFn(prices.length - 1)
  const lastY    = yFn(prices[prices.length - 1]!)
  const firstX   = xFn(0)

  const color  = isUp ? '#00C076' : '#FF3B69'
  const gradId = `cg-${isUp ? 'u' : 'd'}`
  const glowId = `gg-${isUp ? 'u' : 'd'}`

  // 4 subtle horizontal grid lines
  const gridLines = [0.2, 0.4, 0.6, 0.8].map(t => PY + t * (H - PY * 2))

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-36" preserveAspectRatio="none">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor={color} stopOpacity="0.35" />
          <stop offset="70%"  stopColor={color} stopOpacity="0.07" />
          <stop offset="100%" stopColor={color} stopOpacity="0"    />
        </linearGradient>
        <filter id={glowId} x="-5%" y="-50%" width="110%" height="200%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* grid */}
      {gridLines.map((gy, i) => (
        <line key={i} x1={PX} y1={gy} x2={W - PX} y2={gy}
          stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
      ))}

      {/* area fill */}
      <path
        d={`${linePath} L ${lastX.toFixed(2)} ${H} L ${firstX.toFixed(2)} ${H} Z`}
        fill={`url(#${gradId})`}
      />

      {/* main line */}
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
        filter={`url(#${glowId})`}
      />

      {/* live tip: outer pulse ring + inner dot */}
      <circle cx={lastX} cy={lastY} r="7" fill={color} opacity="0.15" />
      <circle cx={lastX} cy={lastY} r="3.5" fill={color} />
    </svg>
  )
}

// ── price formatter ────────────────────────────────────────────────────────
function fmt(v: number): string {
  const dec = v >= 1000 ? 2 : v >= 1 ? 4 : 6
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD',
    minimumFractionDigits: dec, maximumFractionDigits: dec,
  }).format(v)
}

// ── widget ─────────────────────────────────────────────────────────────────
interface Props {
  binanceSymbol: string   // e.g. "BTCUSDT"
  displayName:   string   // e.g. "BTC / USD"
  iconUrl:       string
}

export function CryptoSparklineWidget({ binanceSymbol, displayName, iconUrl }: Props) {
  const [history,   setHistory]   = useState<number[]>([])
  const [current,   setCurrent]   = useState<number | null>(null)
  const [open24h,   setOpen24h]   = useState<number | null>(null)
  const [high24h,   setHigh24h]   = useState<number | null>(null)
  const [low24h,    setLow24h]    = useState<number | null>(null)
  const [volume24h, setVolume24h] = useState<number | null>(null)
  const [connected, setConnected] = useState(false)

  const wsRef         = useRef<WebSocket | null>(null)
  const lastBucketRef = useRef<number>(bucket())
  const tickModeRef   = useRef<boolean>(false)  // true = klines failed, accumulate raw ticks

  // ── historical closes via server-side proxy ────────────────────────────
  useEffect(() => {
    fetch(`/api/klines?symbol=${binanceSymbol}&interval=15m&limit=${MAX_HISTORY}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((d: { closes?: number[] }) => {
        if (d.closes && d.closes.length >= 2) {
          setHistory(d.closes)
          setCurrent(d.closes[d.closes.length - 1]!)
          lastBucketRef.current = bucket()
        } else {
          tickModeRef.current = true  // fall back to tick accumulation
        }
      })
      .catch(() => {
        tickModeRef.current = true  // klines failed — use raw ticks
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [binanceSymbol])

  // ── live price: @miniTicker (fires every ~1 s, very reliable) ─────────
  useEffect(() => {
    let cancelled = false
    const sym = binanceSymbol.toLowerCase()

    function connect() {
      if (cancelled) return
      const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${sym}@miniTicker`)
      wsRef.current = ws

      ws.onopen  = () => { if (!cancelled) setConnected(true) }
      ws.onerror = () => ws.close()
      ws.onclose = () => {
        if (!cancelled) {
          setConnected(false)
          setTimeout(connect, 3000)
        }
      }

      ws.onmessage = (e) => {
        if (cancelled) return
        const msg    = JSON.parse(e.data as string)
        const price  = parseFloat(msg.c)
        const open   = parseFloat(msg.o)
        const high   = parseFloat(msg.h)
        const low    = parseFloat(msg.l)
        const vol    = parseFloat(msg.v)

        setCurrent(price)
        setOpen24h(open)
        setHigh24h(high)
        setLow24h(low)
        setVolume24h(vol)

        if (tickModeRef.current) {
          // Accumulate raw ticks as chart data (klines fallback)
          setHistory(prev => {
            const next = [...prev, price]
            return next.length > MAX_TICKS ? next.slice(-MAX_TICKS) : next
          })
        } else {
          // 15-minute bucket mode: update tip live, append on bucket roll
          const b = bucket()
          if (b !== lastBucketRef.current) {
            lastBucketRef.current = b
            setHistory(prev => [...prev.slice(-(MAX_HISTORY - 1)), price])
          } else {
            setHistory(prev => {
              if (prev.length === 0) return [price]
              return [...prev.slice(0, -1), price]
            })
          }
        }
      }
    }

    connect()
    return () => {
      cancelled = true
      wsRef.current?.close()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [binanceSymbol])

  const pct    = current !== null && open24h !== null ? ((current - open24h) / open24h) * 100 : null
  const isUp   = pct === null ? true : pct >= 0
  const color  = isUp ? '#00C076' : '#FF3B69'
  const bgGlow = isUp ? 'rgba(0,192,118,0.04)' : 'rgba(255,59,105,0.04)'

  return (
    <div
      className="rounded-2xl p-5 flex flex-col gap-3 border border-zinc-800 transition-all"
      style={{ background: `linear-gradient(160deg, #111214 0%, ${bgGlow} 100%)` }}
    >
      {/* ── top row: icon + name + live dot ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={iconUrl} alt={displayName} width={22} height={22} className="rounded-full" />
          <span className="text-sm font-mono font-semibold text-zinc-300 tracking-wide">
            {displayName}
          </span>
          {/* live indicator */}
          <span className={`flex h-2 w-2 relative`}>
            {connected && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-60" />
            )}
            <span className={`relative inline-flex rounded-full h-2 w-2 ${connected ? 'bg-green-400' : 'bg-zinc-600'}`} />
          </span>
        </div>

        {/* % change badge */}
        {pct !== null ? (
          <div
            className="flex items-center gap-1 text-sm font-mono font-bold px-2.5 py-1 rounded-lg"
            style={{ color, background: `${color}18` }}
          >
            <span>{isUp ? '▲' : '▼'}</span>
            <span>{Math.abs(pct).toFixed(2)}%</span>
          </div>
        ) : (
          <div className="text-sm font-mono text-zinc-700 px-2.5 py-1">—</div>
        )}
      </div>

      {/* ── price ── */}
      <div className="flex items-end gap-3">
        <span className="text-3xl font-mono font-bold text-white leading-none tracking-tight">
          {current !== null
            ? fmt(current)
            : <span className="text-zinc-600 animate-pulse text-xl">Loading…</span>
          }
        </span>
      </div>

      {/* ── chart ── */}
      <AreaChart prices={history} isUp={isUp} />

      {/* ── stats row ── */}
      <div className="grid grid-cols-3 gap-2 pt-1 border-t border-zinc-800/60">
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-600">24h High</span>
          <span className="text-xs font-mono text-zinc-300">
            {high24h !== null ? fmt(high24h) : '—'}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-600">24h Low</span>
          <span className="text-xs font-mono text-zinc-300">
            {low24h !== null ? fmt(low24h) : '—'}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-600">Volume</span>
          <span className="text-xs font-mono text-zinc-300">
            {volume24h !== null
              ? volume24h >= 1_000_000
                ? `${(volume24h / 1_000_000).toFixed(2)}M`
                : `${(volume24h / 1_000).toFixed(0)}K`
              : '—'}
          </span>
        </div>
      </div>
    </div>
  )
}
