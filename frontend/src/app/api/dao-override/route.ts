export const dynamic = 'force-dynamic'

import { Transaction } from '@mysten/sui/transactions'
import { suiClient, getGuardianKeypair, getSuiConfig } from '@/lib/suiClient'

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}))
    const reason = (body.reason as string | undefined) ?? 'manual_dao_override'

    const { packageId, riskParamsId, daoCapId } = getSuiConfig()
    const keypair = getGuardianKeypair()
    const encoder = new TextEncoder()

    const tx = new Transaction()
    tx.moveCall({
      target: `${packageId}::guardian::dao_override`,
      arguments: [
        tx.object(daoCapId),
        tx.object(riskParamsId),
        tx.pure.vector('u8', Array.from(encoder.encode(reason))),
      ],
    })

    const result = await suiClient.signAndExecuteTransaction({
      signer: keypair,
      transaction: tx,
      options: { showEvents: true, showEffects: true },
    })

    const network = process.env.SUI_NETWORK ?? 'testnet'
    return Response.json({
      action: 'dao_override',
      digest: result.digest,
      explorerUrl: `https://suiscan.xyz/${network}/tx/${result.digest}`,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DAO override failed'
    return Response.json({ error: message }, { status: 500 })
  }
}
