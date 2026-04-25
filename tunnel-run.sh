#!/usr/bin/env bash
# Named tunnel — custom domain via OpenTofu infra.
# Prerequisites: cd infra && tofu init && tofu apply
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/infra/cloudflare"

if [ ! -f "$INFRA_DIR/terraform.tfstate" ]; then
  echo "ERROR: No tunnel provisioned yet. Run first:"
  echo "  cd infra/cloudflare && tofu init && cp terraform.tfvars.example terraform.tfvars"
  echo "  # Fill in terraform.tfvars, then:"
  echo "  tofu apply"
  exit 1
fi

TOKEN=$(cd "$INFRA_DIR" && tofu output -raw tunnel_token)
URL=$(cd "$INFRA_DIR" && tofu output -raw public_url)

echo "Tunnel → $URL"
cloudflared tunnel run --token "$TOKEN"
