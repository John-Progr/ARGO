'use client'

import { useState } from 'react'
import type { JobStatus, JobPhase } from '@/hooks/useAgentAnalysis'

const AGENTS: { key: string; label: string }[] = [
  { key: 'news',      label: 'News & Sentiment' },
  { key: 'onchain',   label: 'On-Chain Data' },
  { key: 'technical', label: 'Technical Analysis' },
  { key: 'macro',     label: 'Macro Context' },
  { key: 'risk',      label: 'Risk Synthesis' },
]

const STATUS_LABELS: Record<JobPhase, string> = {
  queued:             'QUEUED',
  running:            'RUNNING',
  awaiting_approval:  'AWAITING APPROVAL',
  generating_script:  'GENERATING SCRIPT',
  done:               'DONE',
  rejected:           'REJECTED',
  error:              'ERROR',
}

const STATUS_COLORS: Record<JobPhase, string> = {
  queued:            'text-zinc-400 border-zinc-600',
  running:           'text-yellow-400 border-yellow-800 animate-pulse',
  awaiting_approval: 'text-blue-400 border-blue-700 animate-pulse',
  generating_script: 'text-purple-400 border-purple-700 animate-pulse',
  done:              'text-green-400 border-green-800',
  rejected:          'text-zinc-500 border-zinc-700',
  error:             'text-red-400 border-red-800',
}

const REC_STYLES = {
  BUY:               'text-green-400',
  SELL:              'text-red-400',
  HOLD:              'text-yellow-400',
  'INSUFFICIENT DATA': 'text-zinc-400',
}

interface Props {
  job: JobStatus | null
  submitting: boolean
  error: string | null
  onAnalyze: (amount_usd: number, fidelity: 'LOW' | 'HIGH') => void
  onApprove: () => void
  onReject: () => void
}

export function AgentAnalyzer({ job, submitting, error, onAnalyze, onApprove, onReject }: Props) {
  const [amountUsd, setAmountUsd] = useState('1000')
  const [fidelity, setFidelity] = useState<'LOW' | 'HIGH'>('HIGH')

  const isActive  = job?.status === 'queued' || job?.status === 'running' || job?.status === 'generating_script'
  const isWaiting = job?.status === 'awaiting_approval'
  const verdict   = job?.result && !('error' in job.result) ? (job.result as any) : null
  const resultError = job?.result && ('error' in job.result) ? (job.result as { error: string }).error : null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const usd = parseFloat(amountUsd)
    if (!usd || usd <= 0) return
    onAnalyze(usd, fidelity)
  }

  return (
    <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">
          AI Agent Analysis · SUI
        </span>
        {job && (
          <span className={`text-xs font-mono px-2 py-0.5 rounded border ${STATUS_COLORS[job.status]}`}>
            {STATUS_LABELS[job.status]}
          </span>
        )}
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
        {/* Amount */}
        <div className="flex items-center bg-white dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded-lg px-3 py-2 gap-1.5 flex-1">
          <span className="text-xs font-mono text-zinc-400">$</span>
          <input
            type="number"
            value={amountUsd}
            onChange={e => setAmountUsd(e.target.value)}
            min="1"
            placeholder="1000"
            disabled={submitting || isActive || isWaiting}
            className="flex-1 bg-transparent text-sm font-mono text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none disabled:opacity-50 min-w-0"
          />
        </div>

        {/* Fidelity toggle */}
        <div className="flex rounded-lg overflow-hidden border border-zinc-300 dark:border-zinc-700 shrink-0">
          {(['LOW', 'HIGH'] as const).map(f => (
            <button
              key={f}
              type="button"
              onClick={() => setFidelity(f)}
              disabled={submitting || isActive || isWaiting}
              className={`px-3 py-2 text-xs font-mono font-semibold transition-colors disabled:opacity-50
                ${fidelity === f
                  ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900'
                  : 'bg-white text-zinc-500 dark:bg-zinc-800 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'
                }`}
            >
              {f}
            </button>
          ))}
        </div>

        <button
          type="submit"
          disabled={submitting || isActive || isWaiting}
          className="px-4 py-2 text-sm font-mono font-semibold rounded-lg bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 hover:opacity-80 disabled:opacity-40 transition-opacity shrink-0"
        >
          {submitting ? 'Starting…' : isActive ? 'Running…' : 'Analyze'}
        </button>
      </form>

      {/* Mode hint */}
      <p className="text-xs font-mono text-zinc-500 mb-3">
        {fidelity === 'LOW'
          ? 'LOW — fast 2-agent mode (technical + market scrape, no API keys)'
          : 'HIGH — full 6-agent pipeline (news, on-chain, technical, macro, risk, review)'}
      </p>

      {/* Hook-level error */}
      {error && <p className="text-xs font-mono text-red-400 mb-3">{error}</p>}

      {/* In-flight: agent progress */}
      {isActive && (
        <div className="space-y-2">
          {AGENTS.map(({ key, label }, i) => (
            <div key={key} className="flex items-center gap-2 font-mono text-xs">
              <span
                className="h-1.5 w-1.5 rounded-full bg-yellow-400 animate-pulse shrink-0"
                style={{ animationDelay: `${i * 150}ms` }}
              />
              <span className="text-zinc-500 w-28 shrink-0">{label}</span>
              <span className="text-zinc-600 dark:text-zinc-700">analyzing…</span>
            </div>
          ))}
        </div>
      )}

      {/* Awaiting approval: show verdict + approve/reject */}
      {isWaiting && verdict && (
        <div className="space-y-3">
          <div className="flex items-center gap-4 font-mono">
            <span className={`text-2xl font-bold ${REC_STYLES[verdict.final_recommendation as keyof typeof REC_STYLES] ?? 'text-zinc-400'}`}>
              {verdict.final_recommendation}
            </span>
            <span className="text-sm text-zinc-500">{verdict.overall_confidence}/100 confidence</span>
          </div>
          <p className="text-xs text-zinc-500 font-mono">
            Approve to generate the on-chain Move script, or reject to discard.
          </p>
          <div className="flex gap-2">
            <button
              onClick={onApprove}
              className="flex-1 px-4 py-2 text-sm font-mono font-semibold rounded-lg bg-green-600 text-white hover:bg-green-500 transition-colors"
            >
              Approve — Generate Script
            </button>
            <button
              onClick={onReject}
              className="px-4 py-2 text-sm font-mono font-semibold rounded-lg border border-zinc-400 dark:border-zinc-600 text-zinc-600 dark:text-zinc-400 hover:border-red-400 hover:text-red-400 dark:hover:border-red-500 dark:hover:text-red-400 transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {/* Done with verdict */}
      {job?.status === 'done' && verdict && (
        <div className="flex items-center gap-4 font-mono">
          <span className={`text-2xl font-bold ${REC_STYLES[verdict.final_recommendation as keyof typeof REC_STYLES] ?? 'text-zinc-400'}`}>
            {verdict.final_recommendation}
          </span>
          <span className="text-sm text-zinc-500">{verdict.overall_confidence}/100 confidence</span>
          <span className={`text-xs px-2 py-0.5 rounded ${
            verdict.approved ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'
          }`}>
            {verdict.approved ? 'APPROVED' : 'REJECTED'}
          </span>
        </div>
      )}

      {/* Rejected */}
      {job?.status === 'rejected' && (
        <p className="text-xs font-mono text-zinc-500">Recommendation rejected — no script generated.</p>
      )}

      {/* Result-level error */}
      {resultError && <p className="text-xs font-mono text-red-400">{resultError}</p>}
    </div>
  )
}
