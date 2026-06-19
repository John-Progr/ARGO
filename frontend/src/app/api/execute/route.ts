export const dynamic = 'force-dynamic'

import { Transaction } from '@mysten/sui/transactions'
import { suiClient, getGuardianKeypair, getSuiConfig } from '@/lib/suiClient'
// suiClient is SuiJsonRpcClient (v2 export name) — signAndExecuteTransaction is available

type Recommendation = 'BUY' | 'SELL' | 'HOLD' | 'INSUFFICIENT DATA'

interface ExecuteRequest {
  recommendation: Recommendation
  confidence: number
  approved: boolean
  coin: string
}

interface ExecuteResult {
  action: string
  digest: string
  explorerUrl: string
}

/** Map agent verdict → which contract function to call. */
function pickAction(rec: Recommendation, approved: boolean): 'adjust_parameters' | 'pause_market' | null {
  if (!approved) return null
  if (rec === 'SELL') return 'pause_market'
  if (rec === 'BUY' || rec === 'HOLD') return 'adjust_parameters'
  return null
}

/** Derive conservative LTV from recommendation + confidence. */
function deriveLtv(rec: Recommendation, confidence: number): number {
  if (rec === 'BUY' && confidence >= 80) return 8000  // 80% — bullish signal
  if (rec === 'BUY')                     return 7500  // 75% — cautious bullish
  return 7500                                         // HOLD → keep default
}

export async function POST(req: Request) {
  try {
    const body: ExecuteRequest = await req.json()
    const { recommendation, confidence, approved, coin } = body

    const action = pickAction(recommendation, approved)
    if (!action) {
      return Response.json(
        { skipped: true, reason: `No on-chain action for ${recommendation} / approved=${approved}` },
        { status: 200 }
      )
    }

    const { packageId, riskParamsId, guardianCapId } = getSuiConfig()
    const keypair = getGuardianKeypair()
    const encoder = new TextEncoder()

    const tx = new Transaction()

    if (action === 'pause_market') {
      const reason = encoder.encode(`de_peg_detected:${coin}`)
      tx.moveCall({
        target: `${packageId}::guardian::pause_market`,
        arguments: [
          tx.object(guardianCapId),
          tx.object(riskParamsId),
          tx.pure.vector('u8', Array.from(reason)),
        ],
      })
    } else {
      // adjust_parameters
      const ltv = deriveLtv(recommendation, confidence)
      const rec  = encoder.encode(recommendation)
      tx.moveCall({
        target: `${packageId}::guardian::adjust_parameters`,
        arguments: [
          tx.object(guardianCapId),
          tx.object(riskParamsId),
          tx.pure.u64(ltv),
          tx.pure.u64(1_000_000),
          tx.pure.u64(confidence),
          tx.pure.vector('u8', Array.from(rec)),
        ],
      })
    }

    const result = await suiClient.signAndExecuteTransaction({
      signer: keypair,
      transaction: tx,
      options: { showEvents: true, showEffects: true },
    })

    const network = process.env.SUI_NETWORK ?? 'testnet'
    const explorerUrl = `https://suiscan.xyz/${network}/tx/${result.digest}`

    return Response.json({
      action,
      digest: result.digest,
      explorerUrl,
    } satisfies ExecuteResult)

  } catch (err) {
    const message = err instanceof Error ? err.message : 'Execution failed'
    return Response.json({ error: message }, { status: 500 })
  }
}
