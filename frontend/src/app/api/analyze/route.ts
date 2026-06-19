export const dynamic = 'force-dynamic'

const AGENT_API = process.env.AGENT_API_URL ?? 'http://localhost:8000'

interface AnalyzeRequest {
  amount_usd: number
  fidelity: 'LOW' | 'HIGH'
}

export async function POST(req: Request) {
  try {
    const body: AnalyzeRequest = await req.json()
    const { amount_usd, fidelity } = body

    if (!amount_usd || amount_usd <= 0) {
      return Response.json({ error: 'amount_usd must be greater than 0' }, { status: 400 })
    }
    if (fidelity !== 'LOW' && fidelity !== 'HIGH') {
      return Response.json({ error: 'fidelity must be LOW or HIGH' }, { status: 400 })
    }

    const res = await fetch(`${AGENT_API}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_usd, fidelity }),
    })

    if (!res.ok) {
      return Response.json(
        { error: `Agent service error: ${res.statusText}` },
        { status: res.status }
      )
    }

    const data = await res.json()
    return Response.json(data)
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : 'Failed to trigger analysis' },
      { status: 500 }
    )
  }
}
