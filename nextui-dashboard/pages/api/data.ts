import type { NextApiRequest, NextApiResponse } from 'next'

const ASSETS: Record<string, string> = {
  'BTC/USD': '0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43',
  'ETH/USD': '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace',
  'SUI/USD': '0x23d7315113f5b1d3ba7a83604c44b94d79f4fd69af77f804fc7f920a6dc65744',
}

type RiskLabel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

function riskLabel(score: number): RiskLabel {
  if (score < 15) return 'LOW'
  if (score < 40) return 'MEDIUM'
  if (score < 70) return 'HIGH'
  return 'CRITICAL'
}

export default async function handler(_req: NextApiRequest, res: NextApiResponse) {
  const ids = Object.values(ASSETS)
  const url = new URL('https://hermes.pyth.network/v2/updates/price/latest')
  ids.forEach(id => url.searchParams.append('ids[]', id))

  let pythData
  try {
    const upstream = await fetch(url.toString())
    if (!upstream.ok) return res.status(502).json({ error: 'Pyth unavailable' })
    pythData = await upstream.json()
  } catch {
    return res.status(502).json({ error: 'Network error reaching Pyth' })
  }

  const prices: Record<string, { price: number; conf: number; timestamp: number; confRatio: number }> = {}

  for (const item of pythData.parsed ?? []) {
    const expo: number = item.price.expo
    const scale = Math.pow(10, expo)
    const price = parseFloat(item.price.price) * scale
    const conf = parseFloat(item.price.conf) * scale
    const label = Object.entries(ASSETS).find(([, id]) => id.replace(/^0x/, '') === item.id)?.[0] ?? item.id
    prices[label] = {
      price,
      conf,
      confRatio: price > 0 ? conf / price : 0,
      timestamp: item.price.publish_time,
    }
  }

  const confRatios = Object.values(prices).map(p => p.confRatio)
  const maxConfRatio = Math.max(...confRatios, 0)
  const score = Math.min(100, Math.round(maxConfRatio * 20000))

  return res.status(200).json({
    prices,
    risk: { score, label: riskLabel(score), maxConfRatio },
    fetchedAt: Date.now(),
  })
}
