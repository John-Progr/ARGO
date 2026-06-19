import { useEffect, useState } from 'react'

interface ChainEvent {
  type: string
  txDigest: string
  timestampMs: number | null
  params: Record<string, string>
}

interface RiskParams {
  ltv_bps: number
  borrow_cap: number
  paused: boolean
  pause_reason: string
  action_count: number
}

interface OnChainData {
  events: ChainEvent[]
  riskParams: RiskParams | null
  network: string
  error?: string
  notConfigured?: boolean
}

const EVENT_COLOR: Record<string, string> = {
  ParametersAdjusted: 'text-blue-400',
  MarketPaused:       'text-red-400',
  MarketResumed:      'text-green-400',
  DaoOverrideApplied: 'text-yellow-400',
}

const EVENT_LABEL: Record<string, string> = {
  ParametersAdjusted: 'adjust_parameters',
  MarketPaused:       'pause_market',
  MarketResumed:      'resume_market',
  DaoOverrideApplied: 'dao_override',
}

function formatTime(tsMs: number | null): string {
  if (!tsMs) return '--:--:--'
  return new Date(tsMs).toLocaleTimeString('en-US', { hour12: false })
}

function paramSummary(type: string, p: Record<string, string>): string {
  if (type === 'ParametersAdjusted')
    return `ltv=${(Number(p.ltv_bps) / 100).toFixed(0)}%  rec=${p.recommendation}  conf=${p.confidence}`
  if (type === 'MarketPaused')
    return `reason=${p.reason || '—'}`
  if (type === 'MarketResumed')
    return `by=${p.by?.slice(0, 10)}…`
  if (type === 'DaoOverrideApplied')
    return `action=${p.action}`
  return ''
}

export function OnChainLog() {
  const [data, setData] = useState<OnChainData | null>(null)
  const [fetchError, setFetchError] = useState<string | null>(null)

  async function fetchLog() {
    try {
      const res = await fetch('/api/onchain-log')
      const json: OnChainData = await res.json()
      if (json.error) throw new Error(json.error)
      setData(json)
      setFetchError(null)
    } catch (e) {
      setFetchError(e instanceof Error ? e.message : 'fetch error')
    }
  }

  useEffect(() => {
    fetchLog()
    const id = setInterval(fetchLog, 10_000)
    return () => clearInterval(id)
  }, [])

  const network  = data?.network ?? 'testnet'
  const params   = data?.riskParams
  const events   = data?.events ?? []

  return (
    <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-4 space-y-4">

      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">
            On-Chain Action Log
          </span>

          {/* Live RiskParameters state */}
          {params && (
            <div className="flex items-center gap-3 mt-1.5 font-mono text-xs">
              <span className="text-zinc-500">
                ltv <span className="text-zinc-300">{(params.ltv_bps / 100).toFixed(0)}%</span>
              </span>
              <span className="text-zinc-500">
                cap <span className="text-zinc-300">{params.borrow_cap.toLocaleString()}</span>
              </span>
              <span className="text-zinc-500">
                actions <span className="text-zinc-300">{params.action_count}</span>
              </span>
              {params.paused && (
                <span className="text-red-400 border border-red-800 rounded px-1.5 py-0.5 animate-pulse">
                  MARKET PAUSED
                </span>
              )}
            </div>
          )}
        </div>

        <div className="shrink-0 text-xs font-mono">
          {fetchError ? (
            <span className="text-red-400">{fetchError}</span>
          ) : data?.notConfigured ? (
            <span className="text-zinc-600 border border-zinc-800 rounded px-2 py-0.5">
              not deployed
            </span>
          ) : (
            <span className="text-zinc-400 dark:text-zinc-700 border border-zinc-200 dark:border-zinc-800 rounded px-2 py-0.5">
              {network} · live
            </span>
          )}
        </div>
      </div>

      {/* Event rows */}
      <div className="space-y-1.5">
        {data?.notConfigured ? (
          <p className="text-xs font-mono text-zinc-500 dark:text-zinc-600">
            Contract not deployed — set SUI_PACKAGE_ID and SUI_RISK_PARAMS_ID in .env.local to enable on-chain tracking.
          </p>
        ) : events.length > 0 ? (
          events.map((e, i) => (
            <a
              key={i}
              href={`https://suiscan.xyz/${network}/tx/${e.txDigest}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 font-mono text-xs border border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600 rounded-lg px-3 py-2 transition-colors group"
            >
              <span className="w-16 shrink-0 text-zinc-400 dark:text-zinc-600">
                {formatTime(e.timestampMs)}
              </span>
              <span className={`shrink-0 ${EVENT_COLOR[e.type] ?? 'text-zinc-400'}`}>
                {EVENT_LABEL[e.type] ?? e.type}
              </span>
              <span className="text-zinc-500 truncate">
                {paramSummary(e.type, e.params)}
              </span>
              <span className="ml-auto shrink-0 text-zinc-600 group-hover:text-zinc-400 transition-colors">
                {e.txDigest.slice(0, 8)}…
              </span>
            </a>
          ))
        ) : !fetchError ? (
          <p className="text-xs font-mono text-zinc-500 dark:text-zinc-700">
            No on-chain actions yet — run an analysis to trigger the first transaction.
          </p>
        ) : null}
      </div>
    </div>
  )
}
