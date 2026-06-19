import { SuiClient, getFullnodeUrl } from '@mysten/sui/client'
import { Ed25519Keypair } from '@mysten/sui/keypairs/ed25519'
import { decodeSuiPrivateKey } from '@mysten/sui/cryptography'

type Network = 'testnet' | 'mainnet' | 'devnet'

const NETWORK = (process.env.SUI_NETWORK ?? 'testnet') as Network

export const suiClient = new SuiClient({
  url: getFullnodeUrl(NETWORK),
})

/** Build a keypair from the GUARDIAN_PRIVATE_KEY env var (suiprivkey… format). */
export function getGuardianKeypair(): Ed25519Keypair {
  const raw = process.env.GUARDIAN_PRIVATE_KEY
  if (!raw) throw new Error('GUARDIAN_PRIVATE_KEY is not set')
  const { secretKey } = decodeSuiPrivateKey(raw)
  return Ed25519Keypair.fromSecretKey(secretKey)
}

/** Required object IDs — validated at call time so missing config fails fast. */
export function getSuiConfig() {
  const packageId     = process.env.SUI_PACKAGE_ID
  const riskParamsId  = process.env.SUI_RISK_PARAMS_ID
  const guardianCapId = process.env.GUARDIAN_CAP_ID
  const daoCapId      = process.env.DAO_CAP_ID

  if (!packageId)     throw new Error('SUI_PACKAGE_ID is not set')
  if (!riskParamsId)  throw new Error('SUI_RISK_PARAMS_ID is not set')
  if (!guardianCapId) throw new Error('GUARDIAN_CAP_ID is not set')
  if (!daoCapId)      throw new Error('DAO_CAP_ID is not set')

  return { packageId, riskParamsId, guardianCapId, daoCapId }
}
