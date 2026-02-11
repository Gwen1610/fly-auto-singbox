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
assert_contains '^SUBSCRIPTION_FORMAT="auto"$' "${WORK_DIR}/config/fly.env"
assert_contains '^SUBCONVERTER_URL="http://127.0.0.1:25500/sub"$' "${WORK_DIR}/config/fly.env"
assert_contains '^SUBCONVERTER_AUTO_INSTALL_DOCKER="true"$' "${WORK_DIR}/config/fly.env"
assert_contains '^SUBCONVERTER_AUTO_START_LOCAL="true"$' "${WORK_DIR}/config/fly.env"
assert_contains '^ENABLE_DEPRECATED_SPECIAL_OUTBOUNDS="true"$' "${WORK_DIR}/config/fly.env"

cat > "${WORK_DIR}/config/fly.env" <<'EOF'
SUBSCRIPTION_URL="custom://should-not-keep"
EOF

./fly init --force
assert_contains '^SUBSCRIPTION_URL=""' "${WORK_DIR}/config/fly.env"

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
      "tag": "香港-01",
      "server": "2.2.2.2",
      "server_port": 443,
      "method": "2022-blake3-aes-128-gcm",
      "password": "pass"
    },
    {
      "type": "shadowsocks",
      "tag": "美国-01",
      "server": "3.3.3.3",
      "server_port": 443,
      "method": "2022-blake3-aes-128-gcm",
      "password": "pass"
    },
    {
      "type": "shadowsocks",
      "tag": "日本-01",
      "server": "4.4.4.4",
      "server_port": 443,
      "method": "2022-blake3-aes-128-gcm",
      "password": "pass"
    },
    {
      "type": "shadowsocks",
      "tag": "韩国-01",
      "server": "5.5.5.5",
      "server_port": 443,
      "method": "2022-blake3-aes-128-gcm",
      "password": "pass"
    },
    {
      "type": "shadowsocks",
      "tag": "新加坡-01",
      "server": "6.6.6.6",
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
SUBSCRIPTION_FORMAT="auto"
SUBCONVERTER_URL=""
SINGBOX_VERSION="1.12.20"
INSTALL_DIR="/usr/local/bin"
CONFIG_PATH="/etc/sing-box/config.json"
SERVICE_NAME="sing-box"
INBOUND_MIXED_PORT="7890"
LOG_LEVEL="info"
FINAL_OUTBOUND="proxy"
CHECK_URL="https://www.gstatic.com/generate_204"
ENABLE_DEPRECATED_SPECIAL_OUTBOUNDS="true"
EOF

./fly apply --dry-run
assert_file_exists "${WORK_DIR}/build/config.json"
assert_contains '"outbounds"' "${WORK_DIR}/build/config.json"
assert_contains '"route"' "${WORK_DIR}/build/config.json"
assert_contains '"tag": "us-proxy"' "${WORK_DIR}/build/config.json"
assert_contains '"tag": "hk-proxy"' "${WORK_DIR}/build/config.json"
assert_contains '"tag": "jp-proxy"' "${WORK_DIR}/build/config.json"
assert_contains '"tag": "kr-proxy"' "${WORK_DIR}/build/config.json"
assert_contains '"tag": "sg-proxy"' "${WORK_DIR}/build/config.json"
assert_contains '"outbound": "us-proxy"' "${WORK_DIR}/build/config.json"
assert_contains '"outbound": "hk-proxy"' "${WORK_DIR}/build/config.json"

python3 - "${WORK_DIR}/build/config.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], "r", encoding="utf-8"))
outbounds = {item.get("tag"): item for item in data.get("outbounds", []) if isinstance(item, dict)}

hk_auto = outbounds.get("hk-auto", {})
us_auto = outbounds.get("us-auto", {})
jp_auto = outbounds.get("jp-auto", {})
kr_auto = outbounds.get("kr-auto", {})
sg_auto = outbounds.get("sg-auto", {})

hk_members = hk_auto.get("outbounds", [])
us_members = us_auto.get("outbounds", [])
jp_members = jp_auto.get("outbounds", [])
kr_members = kr_auto.get("outbounds", [])
sg_members = sg_auto.get("outbounds", [])

if "香港-01" not in hk_members:
    raise SystemExit("ASSERT FAIL: hk-auto did not match Chinese HK node tag")
if "美国-01" not in us_members:
    raise SystemExit("ASSERT FAIL: us-auto did not match Chinese US node tag")
if "日本-01" not in jp_members:
    raise SystemExit("ASSERT FAIL: jp-auto did not match Chinese JP node tag")
if "韩国-01" not in kr_members:
    raise SystemExit("ASSERT FAIL: kr-auto did not match Chinese KR node tag")
if "新加坡-01" not in sg_members:
    raise SystemExit("ASSERT FAIL: sg-auto did not match Chinese SG node tag")
PY

mkdir -p "${WORK_DIR}/profile"
FLY_PROXY_HOOK_FILE="${WORK_DIR}/profile/fly-proxy.sh" ./fly proxy-hooks-install
assert_file_exists "${WORK_DIR}/profile/fly-proxy.sh"
assert_contains '^fly_on\(\)' "${WORK_DIR}/profile/fly-proxy.sh"
assert_contains '^fly_off\(\)' "${WORK_DIR}/profile/fly-proxy.sh"
assert_contains '^fly_status\(\)' "${WORK_DIR}/profile/fly-proxy.sh"
source "${WORK_DIR}/profile/fly-proxy.sh"
fly_on >/dev/null
if [[ "${ALL_PROXY:-}" != "socks5://127.0.0.1:7890" ]]; then
  echo "ASSERT FAIL: fly_on did not set ALL_PROXY correctly" >&2
  exit 1
fi
fly_off >/dev/null
if [[ -n "${ALL_PROXY:-}" ]]; then
  echo "ASSERT FAIL: fly_off did not unset ALL_PROXY" >&2
  exit 1
fi

# Dry-run must NOT auto-start local subconverter (docker) when converter is unreachable.
# We put a fake `docker` in PATH that writes a marker file. If fly calls docker, this test fails.
echo "ss://dummy" > "${WORK_DIR}/sub.uri"
cat > "${WORK_DIR}/config/fly.env" <<EOF
SUBSCRIPTION_URL="file://${WORK_DIR}/sub.uri"
SUBSCRIPTION_FILE=""
SUBSCRIPTION_FORMAT="auto"
SUBCONVERTER_URL="http://127.0.0.1:25500/sub"
SUBCONVERTER_AUTO_INSTALL_DOCKER="false"
SUBCONVERTER_AUTO_START_LOCAL="true"
SINGBOX_VERSION="1.12.20"
INSTALL_DIR="/usr/local/bin"
CONFIG_PATH="/etc/sing-box/config.json"
SERVICE_NAME="sing-box"
INBOUND_MIXED_PORT="7890"
LOG_LEVEL="info"
FINAL_OUTBOUND="proxy"
CHECK_URL="https://www.gstatic.com/generate_204"
ENABLE_DEPRECATED_SPECIAL_OUTBOUNDS="true"
EOF

mkdir -p "${WORK_DIR}/bin"
cat > "${WORK_DIR}/bin/docker" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
echo "called" > docker.called
exit 2
SH
chmod +x "${WORK_DIR}/bin/docker"

set +e
PATH="${WORK_DIR}/bin:${PATH}" ./fly apply --dry-run >/dev/null 2>&1
apply_rc=$?
set -e
if [[ "${apply_rc}" -eq 0 ]]; then
  echo "ASSERT FAIL: expected dry-run to fail when local subconverter is unreachable" >&2
  exit 1
fi
if [[ -f "${WORK_DIR}/docker.called" ]]; then
  echo "ASSERT FAIL: dry-run unexpectedly invoked docker (should not auto-start subconverter)" >&2
  exit 1
fi

# Non-dry-run apply should NOT auto-install docker by default.
# Run fly with a PATH that contains only the minimal commands it needs (and no `docker`).
nodocker_bin="${WORK_DIR}/nodockerbin"
mkdir -p "${nodocker_bin}"

real_bash="$(command -v bash)"
real_curl="$(command -v curl)"
real_python3="$(command -v python3)"
real_mkdir="$(command -v mkdir)"
real_dirname="$(command -v dirname)"
real_mktemp="$(command -v mktemp)"
real_rm="$(command -v rm)"

ln -sf "${real_curl}" "${nodocker_bin}/curl"
ln -sf "${real_python3}" "${nodocker_bin}/python3"
ln -sf "${real_mkdir}" "${nodocker_bin}/mkdir"
ln -sf "${real_dirname}" "${nodocker_bin}/dirname"
ln -sf "${real_mktemp}" "${nodocker_bin}/mktemp"
ln -sf "${real_rm}" "${nodocker_bin}/rm"

fly_out="${WORK_DIR}/fly-apply.out"
set +e
PATH="${nodocker_bin}" "${real_bash}" ./fly apply >"${fly_out}" 2>&1
apply_rc=$?
set -e
if [[ "${apply_rc}" -eq 0 ]]; then
  echo "ASSERT FAIL: expected apply to fail when docker is missing and auto-install is disabled" >&2
  exit 1
fi
if ! grep -q "SUBCONVERTER_AUTO_INSTALL_DOCKER" "${fly_out}"; then
  echo "ASSERT FAIL: expected error message to mention SUBCONVERTER_AUTO_INSTALL_DOCKER" >&2
  exit 1
fi

popd >/dev/null
echo "PASS: fly init/apply dry-run"
