import type { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { symbol = 'BTCUSDT', interval = '10m', limit = '72' } = req.query

  try {
    const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`
    const r = await fetch(url)
    if (!r.ok) throw new Error(`Binance ${r.status}`)
    const data = await r.json()
    // Return just the close prices (index 4 in each kline row)
    const closes: number[] = (data as unknown[][]).map(row => parseFloat(row[4] as string))
    res.status(200).json({ closes })
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : 'fetch failed' })
  }
}
