export const dynamic = 'force-dynamic'

const AGENT_API = process.env.AGENT_API_URL ?? 'http://localhost:8000'

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ jobId: string }> }
) {
  try {
    const { jobId } = await params
    const res = await fetch(`${AGENT_API}/approve/${jobId}`, { method: 'POST' })
    const data = await res.json()
    return Response.json(data, { status: res.ok ? 200 : res.status })
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : 'Failed to approve' },
      { status: 500 }
    )
  }
}
