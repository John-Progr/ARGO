import type { AnalysisVerdict } from '@/hooks/useAgentAnalysis'

export type RiskLabel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface RiskData {
  score: number
  label: RiskLabel
  maxConfRatio: number
}

const PALETTE: Record<RiskLabel, { text: string; badge: string; bar: string; border: string; bg: string }> = {
  LOW:      { text: 'text-green-600 dark:text-green-400',   badge: 'text-green-600 bg-green-500/10 dark:text-green-400 dark:bg-green-400/10',   bar: 'bg-green-400',  border: 'border-green-300 dark:border-green-800',   bg: 'bg-green-50 dark:bg-green-950/30' },
  MEDIUM:   { text: 'text-yellow-600 dark:text-yellow-400', badge: 'text-yellow-600 bg-yellow-500/10 dark:text-yellow-400 dark:bg-yellow-400/10', bar: 'bg-yellow-400', border: 'border-yellow-300 dark:border-yellow-800', bg: 'bg-yellow-50 dark:bg-yellow-950/30' },
  HIGH:     { text: 'text-orange-600 dark:text-orange-400', badge: 'text-orange-600 bg-orange-500/10 dark:text-orange-400 dark:bg-orange-400/10', bar: 'bg-orange-400', border: 'border-orange-300 dark:border-orange-800', bg: 'bg-orange-50 dark:bg-orange-950/30' },
  CRITICAL: { text: 'text-red-600 dark:text-red-400',       badge: 'text-red-600 bg-red-500/10 dark:text-red-400 dark:bg-red-400/10',            bar: 'bg-red-400',   border: 'border-red-300 dark:border-red-700',     bg: 'bg-red-50 dark:bg-red-950/30' },
}

// Score bar colours by individual agent score (0-10)
function agentBarColor(score: number): string {
  if (score === 0) return 'bg-red-500'
  if (score <= 3)  return 'bg-red-400'
  if (score <= 5)  return 'bg-orange-400'
  if (score <= 7)  return 'bg-yellow-400'
  return 'bg-green-400'
}

function riskLabelFromScore(score: number): RiskLabel {
  if (score < 20) return 'LOW'
  if (score < 45) return 'MEDIUM'
  if (score < 70) return 'HIGH'
  return 'CRITICAL'
}

// Map individual agent score (0-10) to a risk contribution (0-100)
// Lower agent score = higher risk for that dimension
function agentRiskContribution(score: number): number {
  return Math.round((1 - score / 10) * 100)
}

// Per-fidelity agent keys, weights (already sum to 1.0), and labels
const AGENT_CONFIG: Record<string, { keys: string[]; weights: Record<string, number> }> = {
  LOW: {
    keys:    ['technical', 'market', 'risk'],
    weights: { technical: 0.60, market: 0.25, risk: 0.15 },
  },
  HIGH: {
    keys:    ['news', 'onchain', 'technical', 'macro', 'risk'],
    weights: { news: 0.15, onchain: 0.25, technical: 0.30, macro: 0.15, risk: 0.15 },
  },
}

const AGENT_LABELS: Record<string, string> = {
  news:      'News',
  onchain:   'On-Chain',
  technical: 'Technical',
  market:    'Market',
  macro:     'Macro',
  risk:      'Risk Synth',
}

interface Props {
  risk: RiskData | null
  verdict?: AnalysisVerdict | null
  fidelity?: string | null
}

export function RiskScore({ risk, verdict, fidelity }: Props) {
  // ── Agent-derived mode ───────────────────────────────────────────────
  if (verdict) {
    const scores = verdict.scores

    const modeKey = (fidelity ?? 'HIGH').toUpperCase()
    const config = AGENT_CONFIG[modeKey] ?? AGENT_CONFIG['HIGH']
    const { keys: agentKeys, weights } = config

    // Weighted risk: each agent's "failure" weighted by its importance
    const weightedRisk = agentKeys.reduce((sum, key) => {
      const agentScore = scores[key as keyof typeof scores]?.score ?? 0
      return sum + agentRiskContribution(agentScore) * (weights[key] ?? 0)
    }, 0)

    // Confidence penalty: low overall confidence raises risk further
    const confidencePenalty = (1 - verdict.overall_confidence / 100) * 20
    const riskScore = Math.min(100, Math.round(weightedRisk + confidencePenalty))
    const label = riskLabelFromScore(riskScore)
    const c = PALETTE[label]

    // Find the weakest active agent
    const worstAgent = agentKeys.reduce((worst, key) => {
      const s = scores[key as keyof typeof scores]?.score ?? 0
      const wk = scores[worst as keyof typeof scores]?.score ?? 10
      return s < wk ? key : worst
    }, agentKeys[0])

    return (
      <div className={`border rounded-xl p-6 flex flex-col gap-4 transition-colors duration-700 ${c.bg} ${c.border}`}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">AI Risk Score</span>
          <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${c.badge}`}>{label}</span>
        </div>

        {/* Score */}
        <div className={`text-7xl font-mono font-bold leading-none ${c.text}`}>
          {riskScore}
          <span className="text-3xl text-zinc-400 dark:text-zinc-500 font-normal">%</span>
        </div>

        {/* Bar */}
        <div className="h-2 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-700 ${c.bar}`} style={{ width: `${riskScore}%` }} />
        </div>

        {/* Per-agent breakdown */}
        <div className="space-y-1.5">
          {agentKeys.map(key => {
            const agentScore = scores[key as keyof typeof scores]?.score ?? 0
            return (
              <div key={key} className="flex items-center gap-2 font-mono text-xs">
                <span className="text-zinc-500 w-20 shrink-0">{AGENT_LABELS[key]}</span>
                <div className="flex-1 h-1 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${agentBarColor(agentScore)}`}
                    style={{ width: `${agentScore * 10}%` }}
                  />
                </div>
                <span className="text-zinc-500 w-6 text-right">{agentScore}</span>
              </div>
            )
          })}
        </div>

        {/* Summary line */}
        <p className="text-xs font-mono text-zinc-500">
          Agent confidence {verdict.overall_confidence}/100 ·{' '}
          <span className={
            verdict.final_recommendation === 'BUY'  ? 'text-green-400' :
            verdict.final_recommendation === 'SELL' ? 'text-red-400' :
            'text-yellow-400'
          }>
            {verdict.final_recommendation}
          </span>
          {verdict.failed_agents?.length > 0 && (
            <span className="text-red-400"> · {verdict.failed_agents.length} agent(s) failed</span>
          )}
          {scores[worstAgent as keyof typeof scores]?.score < 5 && (
            <span className="text-orange-400"> · weakest: {AGENT_LABELS[worstAgent]}</span>
          )}
        </p>
      </div>
    )
  }

  // ── Oracle heuristic mode (no verdict yet) ───────────────────────────
  if (!risk) {
    return (
      <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-6 flex items-center justify-center min-h-[200px]">
        <span className="text-zinc-400 dark:text-zinc-600 font-mono text-sm animate-pulse">Fetching risk score…</span>
      </div>
    )
  }

  const { score, label } = risk
  const c = PALETTE[label]

  return (
    <div className={`border rounded-xl p-6 flex flex-col gap-4 transition-colors duration-700 ${c.bg} ${c.border}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Oracle Risk Score</span>
        <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${c.badge}`}>{label}</span>
      </div>

      <div className={`text-7xl font-mono font-bold leading-none ${c.text}`}>
        {score}
        <span className="text-3xl text-zinc-400 dark:text-zinc-500 font-normal">%</span>
      </div>

      <div className="h-2 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${c.bar}`} style={{ width: `${score}%` }} />
      </div>

      <p className="text-xs text-zinc-400 dark:text-zinc-600 font-mono">
        Pyth oracle uncertainty · max confidence interval ratio across BTC, ETH, SUI.
        Run an analysis to activate the AI risk model.
      </p>
    </div>
  )
}
