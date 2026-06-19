export const dynamic = 'force-dynamic'

import { suiClient, getSuiConfig } from '@/lib/suiClient'

function bytesToStr(bytes: unknown): string {
  if (!Array.isArray(bytes) || bytes.length === 0) return ''
  return String.fromCharCode(...(bytes as number[]))
}

export async function GET() {
  try {
    const { packageId, riskParamsId } = getSuiConfig()

    const [eventsRes, paramsRes] = await Promise.all([
      suiClient.queryEvents({
        query: { MoveModule: { package: packageId, module: 'guardian' } },
        limit: 15,
        order: 'descending',
      }),
      suiClient.getObject({
        id: riskParamsId,
        options: { showContent: true },
      }),
    ])

    // Parse events
    const events = eventsRes.data.map(e => {
      const parsed = (e.parsedJson ?? {}) as Record<string, unknown>
      const type = e.type.split('::').pop() ?? e.type

      let params: Record<string, string> = {}
      switch (type) {
        case 'ParametersAdjusted':
          params = {
            ltv_bps:        String(parsed.ltv_bps),
            borrow_cap:     String(parsed.borrow_cap),
            confidence:     String(parsed.confidence),
            recommendation: bytesToStr(parsed.recommendation),
            action_count:   String(parsed.action_count),
          }
          break
        case 'MarketPaused':
          params = {
            reason:       bytesToStr(parsed.reason),
            action_count: String(parsed.action_count),
          }
          break
        case 'MarketResumed':
          params = {
            by:           String(parsed.by),
            action_count: String(parsed.action_count),
          }
          break
        case 'DaoOverrideApplied':
          params = {
            action:       bytesToStr(parsed.action),
            by:           String(parsed.by),
            action_count: String(parsed.action_count),
          }
          break
      }

      return {
        type,
        txDigest:    e.id.txDigest,
        timestampMs: e.timestampMs ? Number(e.timestampMs) : null,
        params,
      }
    })

    // Parse current RiskParameters state from shared object
    let riskParams = null
    const content = paramsRes.data?.content
    if (content && 'fields' in content) {
      const fields = content.fields as Record<string, unknown>
      riskParams = {
        ltv_bps:      Number(fields.ltv_bps),
        borrow_cap:   Number(fields.borrow_cap),
        paused:       Boolean(fields.paused),
        pause_reason: bytesToStr(fields.pause_reason),
        action_count: Number(fields.action_count),
      }
    }

    const network = process.env.SUI_NETWORK ?? 'testnet'
    return Response.json({ events, riskParams, network })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to fetch on-chain data'
    return Response.json({ error: message }, { status: 500 })
  }
}
