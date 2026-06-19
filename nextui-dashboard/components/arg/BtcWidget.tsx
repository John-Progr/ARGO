import { CryptoSparklineWidget } from './CryptoSparklineWidget'

export function BtcWidget() {
  return (
    <CryptoSparklineWidget
      binanceSymbol="BTCUSDT"
      displayName="BTC / USD"
      iconUrl="https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
    />
  )
}
