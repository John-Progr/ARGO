import type { NextApiRequest, NextApiResponse } from 'next'

const AGENT_API = process.env.AGENT_API_URL ?? 'http://localhost:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const { jobId } = req.query

  if (!jobId || typeof jobId !== 'string') {
    return res.status(400).json({ error: 'Missing jobId' })
  }

  try {
    const upstream = await fetch(`${AGENT_API}/result/${jobId}`)

    if (!upstream.ok) {
      return res.status(upstream.status).json({ error: `Agent service error: ${upstream.statusText}` })
    }

    const data = await upstream.json()
    return res.status(200).json(data)
  } catch (error) {
    return res.status(500).json({
      error: error instanceof Error ? error.message : 'Failed to fetch result',
    })
  }
}
