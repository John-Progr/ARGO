const COIN_ICONS: Record<string, string> = {
  'BTC/USD': 'https://assets.coingecko.com/coins/images/1/small/bitcoin.png',
  'ETH/USD': 'https://assets.coingecko.com/coins/images/279/small/ethereum.png',
  'SUI/USD': 'https://assets.coingecko.com/coins/images/26375/small/sui-ocean-square.png',
}

export interface PriceEntry {
  price: number
  conf: number
  timestamp: number
  confRatio: number
}

function ciColor(ratio: number): string {
  if (ratio < 0.00075) return 'text-green-600 bg-green-500/10 dark:text-green-400 dark:bg-green-400/10'
  if (ratio < 0.002)   return 'text-yellow-600 bg-yellow-500/10 dark:text-yellow-400 dark:bg-yellow-400/10'
  if (ratio < 0.0035)  return 'text-orange-600 bg-orange-500/10 dark:text-orange-400 dark:bg-orange-400/10'
  return 'text-red-600 bg-red-500/10 dark:text-red-400 dark:bg-red-400/10'
}

function fmt(value: number): string {
  const decimals = value >= 1000 ? 2 : value >= 1 ? 4 : 6
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function PriceCard({ symbol, data }: { symbol: string; data: PriceEntry | null }) {
  return (
    <div className="bg-zinc-100 border border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800 rounded-xl p-4 flex flex-col gap-1 hover:border-zinc-400 dark:hover:border-zinc-700 transition-colors">
      <div className="flex items-center gap-1.5">
        {COIN_ICONS[symbol] && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={COIN_ICONS[symbol]}
            alt={symbol}
            width={16}
            height={16}
            className="rounded-full"
          />
        )}
        <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">{symbol}</span>
      </div>
      <span className="text-2xl font-mono font-semibold text-zinc-900 dark:text-white">
        {data ? fmt(data.price) : <span className="text-zinc-300 dark:text-zinc-700">—</span>}
      </span>
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-zinc-500">
          {data ? `±${fmt(data.conf)}` : ''}
        </span>
        <span className={`text-xs font-mono rounded px-1 py-0.5 ${data ? ciColor(data.confRatio) : 'text-zinc-300 dark:text-zinc-700'}`}>
          {data ? `${(data.confRatio * 100).toFixed(4)}% ci` : ''}
        </span>
      </div>
    </div>
  )
}
