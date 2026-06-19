export const dynamic = 'force-dynamic'

const AGENT_API = process.env.AGENT_API_URL ?? 'http://localhost:8000'

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ jobId: string }> }
) {
  try {
    const { jobId } = await params

    const res = await fetch(`${AGENT_API}/result/${jobId}`, { cache: 'no-store' })

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
      { error: error instanceof Error ? error.message : 'Failed to fetch result' },
      { status: 500 }
    )
  }
}
