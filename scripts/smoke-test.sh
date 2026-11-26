#!/usr/bin/env bash
# Checks a running stack (docker compose up -d --wait) against the success criteria:
# reachable only through Nginx, upload and ask work, data survives a restart.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; exit 1; }

ask() {
  curl -fsS -H 'content-type: application/json' -d "{\"question\":\"$1\"}" "$BASE_URL/api/ask"
}

[ "$(curl -fsS "$BASE_URL/api/health")" = '{"status":"ok"}' ] && pass "backend health through Nginx" \
  || fail "backend health through Nginx"

curl -fsS "$BASE_URL/" | grep -q "<title>Streamlit</title>" && pass "frontend through Nginx" \
  || fail "frontend through Nginx"

for port in 8000 8501 6333; do
  if curl -s -m 3 -o /dev/null "http://localhost:$port"; then
    fail "port $port is reachable without Nginx"
  fi
done
pass "backend, frontend and Qdrant are not published"

# A relative path, so this also works with Windows curl under Git Bash.
document="smoke-test-$$.txt"
trap 'rm -f "$document"' EXIT
echo "The smoke test marker is purple-elephant-42." > "$document"
curl -fsS -F "file=@$document;filename=smoke.txt" "$BASE_URL/api/upload" | grep -q '"chunks":1' \
  && pass "upload" || fail "upload"

ask "What is the smoke test marker?" | grep -q "purple-elephant-42" && pass "ask returns the document" \
  || fail "ask returns the document"

docker compose down
docker compose up -d --wait --wait-timeout 300
ask "What is the smoke test marker?" | grep -q "purple-elephant-42" \
  && pass "data survives docker compose down and up" || fail "data survives docker compose down and up"
