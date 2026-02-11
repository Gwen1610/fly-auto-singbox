#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

assert_file_exists() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    echo "ASSERT FAIL: expected file exists: ${path}" >&2
    exit 1
  fi
}

assert_contains() {
  local pattern="$1"
  local file="$2"
  if ! grep -qE "${pattern}" "${file}"; then
    echo "ASSERT FAIL: pattern '${pattern}' not found in ${file}" >&2
    exit 1
  fi
}

cp "${ROOT_DIR}/fly" "${WORK_DIR}/fly"
chmod +x "${WORK_DIR}/fly"

pushd "${WORK_DIR}" >/dev/null

./fly init
assert_file_exists "${WORK_DIR}/config/fly.env"
assert_file_exists "${WORK_DIR}/config/groups.json"
assert_file_exists "${WORK_DIR}/config/routes.json"
assert_contains '^SUBSCRIPTION_URL=' "${WORK_DIR}/config/fly.env"

cat > "${WORK_DIR}/subscription.json" <<'JSON'
{
  "outbounds": [
    {
      "type": "shadowsocks",
      "tag": "HK-1",
      "server": "1.1.1.1",
      "server_port": 443,
      "method": "2022-blake3-aes-128-gcm",
      "password": "pass"
    },
    {
      "type": "shadowsocks",
      "tag": "SG-1",
      "server": "2.2.2.2",
      "server_port": 443,
      "method": "2022-blake3-aes-128-gcm",
      "password": "pass"
    }
  ]
}
JSON

cat > "${WORK_DIR}/config/fly.env" <<EOF
SUBSCRIPTION_URL=""
SUBSCRIPTION_FILE="${WORK_DIR}/subscription.json"
SUBSCRIPTION_FORMAT="singbox"
SUBCONVERTER_URL=""
SINGBOX_VERSION="1.12.20"
INSTALL_DIR="/usr/local/bin"
CONFIG_PATH="/etc/sing-box/config.json"
SERVICE_NAME="sing-box"
INBOUND_MIXED_PORT="7890"
LOG_LEVEL="info"
FINAL_OUTBOUND="proxy"
CHECK_URL="https://www.gstatic.com/generate_204"
EOF

./fly apply --dry-run
assert_file_exists "${WORK_DIR}/build/config.json"
assert_contains '"outbounds"' "${WORK_DIR}/build/config.json"
assert_contains '"route"' "${WORK_DIR}/build/config.json"

popd >/dev/null
echo "PASS: fly init/apply dry-run"
