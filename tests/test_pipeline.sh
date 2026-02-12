#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

assert_file_exists() {
  local path="$1"
  [[ -f "${path}" ]] || {
    echo "ASSERT FAIL: missing file ${path}" >&2
    exit 1
  }
}

assert_contains() {
  local pattern="$1"
  local path="$2"
  grep -qE "${pattern}" "${path}" || {
    echo "ASSERT FAIL: pattern '${pattern}' not found in ${path}" >&2
    exit 1
  }
}

cp -R "${ROOT_DIR}" "${WORK_DIR}/repo"
cd "${WORK_DIR}/repo"

./fly init
assert_file_exists "./config/fly.env"
assert_file_exists "./config/extract.providers.json"
assert_file_exists "./config/route-rules.json"
assert_file_exists "./config/base-template.json"

mkdir -p "./mock-subscribe" "./bin"
cat > "./mock-subscribe/main.py" <<'PY'
#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--temp_json_data", required=True)
args = parser.parse_args()

payload = json.loads(args.temp_json_data)
output = Path(payload["save_config_path"])
output.parent.mkdir(parents=True, exist_ok=True)
nodes = [
    {"type": "shadowsocks", "tag": "US-01", "server": "1.1.1.1", "server_port": 443, "method": "aes-128-gcm", "password": "x"},
    {"type": "shadowsocks", "tag": "香港-01", "server": "2.2.2.2", "server_port": 443, "method": "aes-128-gcm", "password": "x"},
    {"type": "shadowsocks", "tag": "JP-01", "server": "3.3.3.3", "server_port": 443, "method": "aes-128-gcm", "password": "x"},
    {"type": "shadowsocks", "tag": "Singapore-01", "server": "4.4.4.4", "server_port": 443, "method": "aes-128-gcm", "password": "x"}
]
output.write_text(json.dumps(nodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"mock saved: {output}")
PY
chmod +x "./mock-subscribe/main.py"

cat > "./bin/sing-box" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "run" ]]; then
  shift
  while true; do
    sleep 1
  done
fi
if [[ "${1:-}" == "version" ]]; then
  echo "sing-box mock"
  exit 0
fi
echo "mock sing-box unsupported args: $*" >&2
exit 2
SH
chmod +x "./bin/sing-box"

cat > "./config/fly.env" <<EOF
SUBSCRIBE_DIR="./mock-subscribe"
PYTHON_BIN="python3"
SING_BOX_BIN="./bin/sing-box"
SUDO_BIN=""
EXTRACT_PROVIDERS_FILE="./config/extract.providers.json"
NODES_FILE="./build/nodes.json"
ROUTE_RULES_FILE="./config/route-rules.json"
BASE_TEMPLATE_FILE="./config/base-template.json"
CONFIG_JSON="./config.json"
PID_FILE="./.sing-box.pid"
LOG_FILE="./sing-box.log"
SINGBOX_VERSION="1.12.20"
EOF

./fly extract
assert_file_exists "./build/nodes.json"
assert_contains '"tag": "US-01"' "./build/nodes.json"
assert_contains '"tag": "香港-01"' "./build/nodes.json"

./fly build-config
assert_file_exists "./config.json"
assert_contains '"tag": "Proxy"' "./config.json"
assert_contains '"tag": "America"' "./config.json"
assert_contains '"tag": "HongKong"' "./config.json"
assert_contains '"outbound": "America"' "./config.json"

./fly pipeline
assert_file_exists "./config.json"

./fly install-guide > "${WORK_DIR}/install-guide.out"
assert_contains 'curl -fL' "${WORK_DIR}/install-guide.out"
assert_contains 'sing-box version' "${WORK_DIR}/install-guide.out"

./fly on
assert_file_exists "./.sing-box.pid"
pid_before="$(cat ./.sing-box.pid)"
status_out="$(./fly status)"
if [[ "${status_out}" != running* ]]; then
  echo "ASSERT FAIL: expected running status, got '${status_out}'" >&2
  exit 1
fi

on_again="$(./fly on)"
if [[ "${on_again}" != already\ running* ]]; then
  echo "ASSERT FAIL: expected idempotent on output, got '${on_again}'" >&2
  exit 1
fi
pid_after="$(cat ./.sing-box.pid)"
if [[ "${pid_before}" != "${pid_after}" ]]; then
  echo "ASSERT FAIL: pid changed on repeated fly on" >&2
  exit 1
fi

echo "line" >> "./sing-box.log"
./fly log --no-follow -n 1 >/dev/null

./fly off
status_after="$(./fly status)"
if [[ "${status_after}" != "not running" ]]; then
  echo "ASSERT FAIL: expected not running after off, got '${status_after}'" >&2
  exit 1
fi

off_again="$(./fly off)"
if [[ "${off_again}" != "not running" ]]; then
  echo "ASSERT FAIL: expected idempotent off output, got '${off_again}'" >&2
  exit 1
fi

echo "PASS: decoupled pipeline + runtime commands"
