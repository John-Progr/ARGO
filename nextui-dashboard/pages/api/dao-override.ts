import type { NextApiRequest, NextApiResponse } from 'next'
import { Transaction } from '@mysten/sui/transactions'
import { suiClient, getGuardianKeypair, getSuiConfig } from '@/lib/suiClient'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const body = req.body ?? {}
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
    return res.status(200).json({
      action: 'dao_override',
      digest: result.digest,
      explorerUrl: `https://suiscan.xyz/${network}/tx/${result.digest}`,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'DAO override failed'
    return res.status(500).json({ error: message })
  }
}
