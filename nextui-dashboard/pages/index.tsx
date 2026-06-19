import type { NextPage } from 'next'
import { useEffect, useRef, useState } from 'react'
import { PriceCard } from '../components/arg/PriceCard'
import type { PriceEntry } from '../components/arg/PriceCard'
import { RiskScore } from '../components/arg/RiskScore'
import type { RiskData } from '../components/arg/RiskScore'
import { ActionLog } from '../components/arg/ActionLog'
import { BtcWidget } from '../components/arg/BtcWidget'
import { SuiWidget } from '../components/arg/SuiWidget'
import { AgentAnalyzer } from '../components/arg/AgentAnalyzer'
import { TradeParameters } from '../components/arg/TradeParameters'
import { OnChainLog } from '../components/arg/OnChainLog'
import { useAgentAnalysis } from '../hooks/useAgentAnalysis'

interface DashboardData {
  prices: Record<string, PriceEntry>
  risk: RiskData
  fetchedAt: number
}

interface TxResult {
  action: string
  digest: string
  explorerUrl: string
}

const SYMBOLS = ['SUI/USD']

const Dashboard: NextPage = () => {
  const [data, setData] = useState<DashboardData | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [oracleError, setOracleError] = useState<string | null>(null)

  // Guardian autonomous execution state
  const [executing, setExecuting] = useState(false)
  const [txResult, setTxResult] = useState<TxResult | null>(null)
  const [txError, setTxError] = useState<string | null>(null)
  const autoExecutedJob = useRef<string | null>(null)

  // DAO override state
  const [daoOverriding, setDaoOverriding] = useState(false)
  const [daoResult, setDaoResult] = useState<TxResult | null>(null)
  const [daoError, setDaoError] = useState<string | null>(null)

  const { job, jobId, submitting, error: analysisError, analyze, approve, reject, verdict } = useAgentAnalysis()

  async function poll() {
    try {
      const res = await fetch('/api/data')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json: DashboardData = await res.json()
      setData(json)
      setLastUpdated(new Date())
      setOracleError(null)
    } catch (e) {
      setOracleError(e instanceof Error ? e.message : 'Unknown error')
    }
  }

  useEffect(() => {
    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Reset all execution state when a new analysis starts
  useEffect(() => {
    if (job?.status === 'queued') {
      setTxResult(null)
      setTxError(null)
      setDaoResult(null)
      setDaoError(null)
    }
  }, [job?.status])

  // Autonomous execution: fires automatically when an approved verdict arrives
  useEffect(() => {
    if (!verdict || !jobId) return
    if (autoExecutedJob.current === jobId) return  // already triggered for this job
    if (executing || txResult) return

    autoExecutedJob.current = jobId

    if (!verdict.approved) return  // rejected verdict — do not execute

    ;(async () => {
      setExecuting(true)
      setTxError(null)
      try {
        const res = await fetch('/api/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            recommendation: verdict.final_recommendation,
            confidence: verdict.overall_confidence,
            approved: verdict.approved,
            coin: job?.coin ?? '',
          }),
        })
        const json = await res.json()
        if (json.error) throw new Error(json.error)
        if (json.skipped) {
          setTxError(`Skipped: ${json.reason}`)
        } else {
          setTxResult(json as TxResult)
        }
      } catch (e) {
        setTxError(e instanceof Error ? e.message : 'Execution failed')
      } finally {
        setExecuting(false)
      }
    })()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [verdict, jobId])

  async function daoOverride() {
    setDaoOverriding(true)
    setDaoError(null)
    try {
      const res = await fetch('/api/dao-override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'human_override' }),
      })
      const json = await res.json()
      if (json.error) throw new Error(json.error)
      setDaoResult(json as TxResult)
    } catch (e) {
      setDaoError(e instanceof Error ? e.message : 'DAO override failed')
    } finally {
      setDaoOverriding(false)
    }
  }

  const lastSeen = lastUpdated
    ? lastUpdated.toLocaleTimeString('en-US', { hour12: false })
    : 'connecting…'

  return (
    <div className="p-6 min-h-full">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Risk score */}
        <RiskScore risk={data?.risk ?? null} verdict={verdict} fidelity={job?.fidelity} />

        {/* Live price charts — side by side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <BtcWidget />
          <SuiWidget />
        </div>

        {/* AI agent analysis trigger */}
        <AgentAnalyzer
          job={job}
          submitting={submitting}
          error={analysisError}
          onAnalyze={analyze}
          onApprove={approve}
          onReject={reject}
        />

        {/* Results: agent scorecard + trade parameters */}
        {verdict && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ActionLog scores={verdict.scores} coin={job?.coin} txResult={txResult ?? undefined} />
              <TradeParameters
                params={verdict.trade_parameters}
                coin={job?.coin ?? ''}
                recommendation={verdict.final_recommendation}
                confidence={verdict.recommendation_confidence}
                approved={verdict.approved}
                reason={verdict.reason}
                invalidation={verdict.invalidation_conditions ?? []}
              />
            </div>

            {/* Autonomous on-chain execution */}
            <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-5">
              <p className="font-mono text-xs uppercase tracking-wider text-zinc-500 mb-3">
                Autonomous on-chain execution
              </p>
              <div className="flex items-center gap-2 text-sm font-mono">
                {executing ? (
                  <>
                    <span className="h-2 w-2 rounded-full bg-yellow-400 animate-pulse shrink-0" />
                    <span className="text-yellow-400">Auto-submitting to Sui testnet…</span>
                  </>
                ) : txResult ? (
                  <>
                    <span className="h-2 w-2 rounded-full bg-green-400 shrink-0" />
                    <a
                      href={txResult.explorerUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-green-400 hover:underline"
                    >
                      {txResult.action} · {txResult.digest.slice(0, 12)}…
                    </a>
                  </>
                ) : txError ? (
                  <>
                    <span className="h-2 w-2 rounded-full bg-red-400 shrink-0" />
                    <span className="text-red-400">{txError}</span>
                  </>
                ) : (
                  <>
                    <span className="h-2 w-2 rounded-full bg-zinc-500 shrink-0" />
                    <span className="text-zinc-500">
                      {verdict.approved
                        ? 'Verdict not approved — no on-chain action.'
                        : 'Verdict rejected — no on-chain action.'}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* DAO human override */}
            <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-5 flex items-center justify-between gap-4">
              <div className="space-y-1">
                <p className="font-mono text-xs uppercase tracking-wider text-zinc-500">
                  DAO human override
                </p>
                <p className="text-xs text-zinc-500 dark:text-zinc-600">
                  Resets LTV to 75%, lifts any pause, and emits a{' '}
                  <code className="text-zinc-400">DaoOverrideApplied</code> event.
                </p>
                {daoResult ? (
                  <a
                    href={daoResult.explorerUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-xs font-mono text-green-400 hover:underline"
                  >
                    override submitted · {daoResult.digest.slice(0, 12)}…
                  </a>
                ) : daoError ? (
                  <p className="text-xs font-mono text-red-400">{daoError}</p>
                ) : null}
              </div>

              <button
                onClick={daoOverride}
                disabled={daoOverriding || !!daoResult}
                className="shrink-0 px-5 py-2 text-sm font-mono font-semibold rounded-lg bg-red-600 text-white hover:bg-red-500 disabled:opacity-40 transition-colors"
              >
                {daoOverriding ? 'Overriding…' : daoResult ? 'Overridden' : 'DAO Override'}
              </button>
            </div>
          </>
        )}

        {/* Live on-chain event log — always visible */}
        <OnChainLog />
      </div>
    </div>
  )
}

export default Dashboard
