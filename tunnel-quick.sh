#!/usr/bin/env bash
# Quick tunnel — instant random trycloudflare.com URL, no config needed.
# Usage: ./tunnel-quick.sh [port]
PORT=${1:-5173}
echo "Starting quick tunnel → 127.0.0.1:$PORT"
echo "URL will appear below (trycloudflare.com)"
cloudflared tunnel --url http://127.0.0.1:$PORT
