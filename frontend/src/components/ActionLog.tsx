import type { AgentScore } from '@/hooks/useAgentAnalysis'

const AGENT_LABELS: Record<string, string> = {
  news:      'News & Sentiment',
  onchain:   'On-Chain Data',
  technical: 'Technical Analysis',
  macro:     'Macro Context',
  risk:      'Risk Synthesis',
}

const PLACEHOLDER_ENTRIES = [
  { time: '--:--:--', action: 'adjust_parameters', params: 'ltv_bps=7500, borrow_cap=1000000' },
  { time: '--:--:--', action: 'pause_market',       params: 'reason=de_peg_detected' },
  { time: '--:--:--', action: 'dao_override',        params: 'restore_ltv, resume_market' },
]

interface TxResult {
  action: string
  digest: string
  explorerUrl: string
}

interface Props {
  scores?: Record<string, AgentScore>
  coin?: string
  txResult?: TxResult
}

export function ActionLog({ scores, coin, txResult }: Props) {
  if (!scores) {
    return (
      <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">On-Chain Action Log</span>
          <span className="text-xs font-mono text-zinc-400 dark:text-zinc-700 border border-zinc-200 dark:border-zinc-800 rounded px-2 py-0.5">
            Pending Move contract
          </span>
        </div>
        <div className="space-y-2">
          {PLACEHOLDER_ENTRIES.map((entry, i) => (
            <div
              key={i}
              className="flex items-center gap-4 font-mono text-xs text-zinc-400 dark:text-zinc-700 border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2"
            >
              <span className="w-16 shrink-0">{entry.time}</span>
              <span className="text-zinc-500 shrink-0">{entry.action}</span>
              <span className="truncate">{entry.params}</span>
              <span className="ml-auto shrink-0 border border-zinc-200 dark:border-zinc-800 rounded px-1.5 py-0.5">pending</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-zinc-400 dark:text-zinc-700 font-mono mt-3">
          Entries populate once the Sui Move policy contract is deployed and the guardian submits its first tx.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Agent Scorecard</span>
        {coin && (
          <span className="text-xs font-mono text-zinc-400 border border-zinc-200 dark:border-zinc-800 rounded px-2 py-0.5">
            {coin}
          </span>
        )}
      </div>
      {txResult && (
        <div className="mb-3 flex items-center gap-2 font-mono text-xs border border-green-800 rounded-lg px-3 py-2 bg-green-400/5">
          <span className="h-1.5 w-1.5 rounded-full bg-green-400 shrink-0" />
          <span className="text-green-400 shrink-0">{txResult.action}</span>
          <a
            href={txResult.explorerUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-400 hover:text-green-400 transition-colors truncate"
          >
            {txResult.digest.slice(0, 16)}…
          </a>
        </div>
      )}

      <div className="space-y-2">
        {Object.entries(scores).map(([key, data]) => {
          const pct = (data.score / 10) * 100
          const barColor =
            data.score >= 7 ? 'bg-green-400' :
            data.score >= 4 ? 'bg-yellow-400' :
            'bg-red-400'
          return (
            <div
              key={key}
              className="border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-xs text-zinc-500">
                  {AGENT_LABELS[key] ?? key}
                </span>
                <span className="font-mono text-xs font-bold text-zinc-400">
                  {data.score}/10
                </span>
              </div>
              <div className="h-1 bg-zinc-200 dark:bg-zinc-700 rounded-full overflow-hidden mb-1.5">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <p className="font-mono text-xs text-zinc-400 dark:text-zinc-600 leading-snug">
                {data.reason}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
