#!/usr/bin/env bash
# Deploy the risk_guardian package to Sui testnet.
# Prerequisites: Sui CLI installed (https://docs.sui.io/guides/developer/getting-started/sui-install)
#                Active wallet with testnet SUI (sui client faucet)
set -e

echo "==> Switching to testnet..."
sui client switch --env testnet

echo "==> Building package..."
sui move build --path "$(dirname "$0")/.."

echo "==> Publishing to testnet..."
RESULT=$(sui client publish \
  --path "$(dirname "$0")/.." \
  --gas-budget 100000000 \
  --json)

echo "$RESULT" | tee contracts/deploy_result.json

PACKAGE_ID=$(echo "$RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for obj in data.get('objectChanges', []):
    if obj.get('type') == 'published':
        print(obj['packageId'])
        break
")

echo ""
echo "================================================================"
echo "  Package ID : $PACKAGE_ID"
echo "  Save this in your .env as: SUI_PACKAGE_ID=$PACKAGE_ID"
echo "================================================================"
