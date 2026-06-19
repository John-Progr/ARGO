import type { NextApiRequest, NextApiResponse } from 'next'
import { suiClient } from '@/lib/suiClient'

const SUI_ID_RE = /^0x[0-9a-fA-F]{64}$/

function isValidSuiId(id: string | undefined): id is string {
  return !!id && SUI_ID_RE.test(id)
}

function bytesToStr(bytes: unknown): string {
  if (!Array.isArray(bytes) || bytes.length === 0) return ''
  return String.fromCharCode(...(bytes as number[]))
}

export default async function handler(_req: NextApiRequest, res: NextApiResponse) {
  const packageId    = process.env.SUI_PACKAGE_ID
  const riskParamsId = process.env.SUI_RISK_PARAMS_ID
  const network      = process.env.SUI_NETWORK ?? 'testnet'

  // Return a clean "not configured" state when IDs are placeholders
  if (!isValidSuiId(packageId) || !isValidSuiId(riskParamsId)) {
    return res.status(200).json({
      events: [],
      riskParams: null,
      network,
      notConfigured: true,
    })
  }

  try {
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
          params = { reason: bytesToStr(parsed.reason), action_count: String(parsed.action_count) }
          break
        case 'MarketResumed':
          params = { by: String(parsed.by), action_count: String(parsed.action_count) }
          break
        case 'DaoOverrideApplied':
          params = { action: bytesToStr(parsed.action), by: String(parsed.by), action_count: String(parsed.action_count) }
          break
      }

      return { type, txDigest: e.id.txDigest, timestampMs: e.timestampMs ? Number(e.timestampMs) : null, params }
    })

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

    return res.status(200).json({ events, riskParams, network })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to fetch on-chain data'
    return res.status(500).json({ error: message })
  }
}
