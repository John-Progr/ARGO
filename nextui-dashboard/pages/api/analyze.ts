import type { NextApiRequest, NextApiResponse } from 'next'

const AGENT_API = process.env.AGENT_API_URL ?? 'http://localhost:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const { amount_usd, fidelity } = req.body

    if (!amount_usd || amount_usd <= 0) {
      return res.status(400).json({ error: 'amount_usd must be greater than 0' })
    }
    if (fidelity !== 'LOW' && fidelity !== 'HIGH') {
      return res.status(400).json({ error: 'fidelity must be LOW or HIGH' })
    }

    const upstream = await fetch(`${AGENT_API}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_usd, fidelity }),
    })

    if (!upstream.ok) {
      return res.status(upstream.status).json({ error: `Agent service error: ${upstream.statusText}` })
    }

    const data = await upstream.json()
    return res.status(200).json(data)
  } catch (error) {
    return res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to trigger analysis',
    })
  }
}
