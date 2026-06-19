import type { TradeParams } from '@/hooks/useAgentAnalysis'

const REC_STYLES: Record<string, { text: string; bg: string }> = {
  BUY:               { text: 'text-green-400',  bg: 'bg-green-400/10' },
  SELL:              { text: 'text-red-400',    bg: 'bg-red-400/10' },
  HOLD:              { text: 'text-yellow-400', bg: 'bg-yellow-400/10' },
  'INSUFFICIENT DATA': { text: 'text-zinc-400', bg: 'bg-zinc-400/10' },
}

interface Props {
  params: TradeParams
  coin: string
  recommendation: string
  confidence: string
  approved: boolean
  reason: string
  invalidation: string[]
}

export function TradeParameters({
  params,
  coin,
  recommendation,
  confidence,
  approved,
  reason,
  invalidation,
}: Props) {
  const rec = REC_STYLES[recommendation] ?? REC_STYLES['INSUFFICIENT DATA']

  return (
    <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">
          Trade Parameters · {coin}
        </span>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${rec.text} ${rec.bg}`}>
            {recommendation}
          </span>
          <span className={`text-xs font-mono px-2 py-0.5 rounded border ${
            approved
              ? 'text-green-400 border-green-800'
              : 'text-red-400 border-red-800'
          }`}>
            {confidence}
          </span>
        </div>
      </div>

      {/* Price levels */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <Field label="Entry Range"   value={params.entry_range} />
        <Field label="Stop Loss"     value={params.stop_loss} />
        <Field label="Take Profit 1" value={params.take_profit_1} />
        <Field label="Take Profit 2" value={params.take_profit_2} />
      </div>

      {/* Position sizing */}
      <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 mb-3">
        <span className="text-xs font-mono text-zinc-500 block mb-2 uppercase tracking-wider">
          Position Size
        </span>
        <div className="grid grid-cols-3 gap-2">
          <SizeField label="Conservative" value={params.position_size?.conservative} />
          <SizeField label="Medium"       value={params.position_size?.medium} />
          <SizeField label="Aggressive"   value={params.position_size?.aggressive} />
        </div>
      </div>

      {/* Summary reason */}
      {reason && (
        <p className="font-mono text-xs text-zinc-400 dark:text-zinc-600 leading-snug mb-3">
          {reason}
        </p>
      )}

      {/* Invalidation conditions */}
      {invalidation.length > 0 && (
        <div>
          <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">
            Invalidation
          </span>
          <ul className="mt-1 space-y-0.5">
            {invalidation.map((cond, i) => (
              <li key={i} className="flex gap-1.5 font-mono text-xs text-zinc-400 dark:text-zinc-600">
                <span className="text-zinc-600 shrink-0">·</span>
                <span>{cond}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function Field({ label, value }: { label: string; value?: string }) {
  return (
    <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2">
      <span className="font-mono text-xs text-zinc-500 block">{label}</span>
      <span className="font-mono text-sm font-semibold text-zinc-900 dark:text-white">
        {value || '—'}
      </span>
    </div>
  )
}

function SizeField({ label, value }: { label: string; value?: string }) {
  return (
    <div className="text-center">
      <span className="font-mono text-xs text-zinc-600 dark:text-zinc-700 block">{label}</span>
      <span className="font-mono text-sm font-bold text-zinc-900 dark:text-white">
        {value || '—'}
      </span>
    </div>
  )
}
