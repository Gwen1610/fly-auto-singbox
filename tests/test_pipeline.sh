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

assert_not_contains() {
  local pattern="$1"
  local path="$2"
  if grep -qE "${pattern}" "${path}"; then
    echo "ASSERT FAIL: pattern '${pattern}' should not appear in ${path}" >&2
    exit 1
  fi
}

cp -R "${ROOT_DIR}" "${WORK_DIR}/repo"
cd "${WORK_DIR}/repo"

./fly init
assert_file_exists "./config/fly.env"
assert_file_exists "./config/extract.providers.json"
assert_file_exists "./config/rule-sources.json"
assert_file_exists "./config/group-strategy.json"
assert_file_exists "./config/route-rules.json"
assert_file_exists "./config/base-template.json"

mkdir -p "./build" "./bin"
cat > "./build/subscription_a.txt" <<'EOF'
ss://YWVzLTEyOC1nY206cGFzcw==@1.1.1.1:443#A-US-01
ss://YWVzLTEyOC1nY206cGFzcw==@2.2.2.2:443#A-HK-01
ss://YWVzLTEyOC1nY206cGFzcw==@3.3.3.3:443#A-JP-01
EOF
cat > "./build/subscription_b.txt" <<'EOF'
ss://YWVzLTEyOC1nY206cGFzcw==@4.4.4.4:443#B-US-01
ss://YWVzLTEyOC1nY206cGFzcw==@5.5.5.5:443#B-HK-01
ss://YWVzLTEyOC1nY206cGFzcw==@6.6.6.6:443#B-SG-01
EOF
cat > "./config/extract.providers.json" <<'JSON'
{
  "subscribes": [
    {
      "tag": "A",
      "enabled": true,
      "url": "./build/subscription_a.txt",
      "prefix": "",
      "emoji": 0
    },
    {
      "tag": "B",
      "enabled": true,
      "url": "./build/subscription_b.txt",
      "prefix": "",
      "emoji": 0
    }
  ]
}
JSON
cat > "./config/group-strategy.json" <<'JSON'
{
  "region_defaults": {
    "HongKong": "A"
  },
  "custom_groups": [
    {
      "tag": "Streaming",
      "members": [
        "HongKong",
        "America"
      ],
      "default": "HongKong"
    },
    {
      "tag": "AI",
      "members": [
        "HongKong",
        "America"
      ],
      "default": "HongKong"
    }
  ],
  "proxy": {
    "members": [
      "Streaming",
      "AI",
      "HongKong",
      "America",
      "Singapore",
      "Japan"
    ],
    "default": "HongKong"
  }
}
JSON
cat > "./config/route-rules.json" <<'JSON'
{
  "final": "Proxy",
  "rules": []
}
JSON

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
  echo "sing-box version 1.12.20"
  exit 0
fi
echo "mock sing-box unsupported args: $*" >&2
exit 2
SH
chmod +x "./bin/sing-box"

cat > "./config/fly.env" <<EOF
PYTHON_BIN="python3"
SING_BOX_BIN="./bin/sing-box"
SUDO_BIN=""
EXTRACT_PROVIDERS_FILE="./config/extract.providers.json"
RULE_SOURCES_FILE="./config/rule-sources.json"
GROUP_STRATEGY_FILE="./config/group-strategy.json"
NODES_FILE="./build/nodes.json"
ROUTE_RULES_FILE="./config/route-rules.json"
BASE_TEMPLATE_FILE="./config/base-template.json"
CONFIG_JSON="./config.json"
PID_FILE="./.sing-box.pid"
LOG_FILE="./sing-box.log"
SINGBOX_VERSION="1.12.20"
SINGBOX_INSTALL_DIR="./bin-install"
EOF

./fly extract
assert_file_exists "./build/nodes.json"
assert_contains '"tag": "A-US-01"' "./build/nodes.json"
assert_contains '"tag": "A-HK-01"' "./build/nodes.json"
assert_contains '"tag": "A-JP-01"' "./build/nodes.json"
assert_contains '"tag": "B-SG-01"' "./build/nodes.json"

./fly build-config
assert_file_exists "./config.json"
assert_contains '"tag": "Proxy"' "./config.json"
assert_contains '"tag": "America"' "./config.json"
assert_contains '"tag": "HongKong"' "./config.json"
assert_contains '"tag": "A-HongKong"' "./config.json"
assert_contains '"tag": "B-HongKong"' "./config.json"
assert_contains '"tag": "Streaming"' "./config.json"
assert_contains '"tag": "AI"' "./config.json"
assert_not_contains 'geosite' "./config.json"
assert_not_contains 'geoip' "./config.json"
python3 - <<'PY'
import json

with open("./config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

route = cfg.get("route", {})
if route.get("final") != "Proxy":
    raise SystemExit("ASSERT FAIL: route.final is not Proxy")

rules = route.get("rules")
if not isinstance(rules, list):
    raise SystemExit("ASSERT FAIL: route.rules is not array")
if len(rules) < 3:
    raise SystemExit("ASSERT FAIL: expected connectivity rules to be injected by default")
if not any(isinstance(item, dict) and item.get("action") == "hijack-dns" for item in rules):
    raise SystemExit("ASSERT FAIL: expected hijack-dns rule to be injected")
if not any(
    isinstance(item, dict)
    and item.get("action") == "reject"
    and any(isinstance(rule, dict) and rule.get("protocol") == "quic" for rule in item.get("rules", []))
    for item in rules
):
    raise SystemExit("ASSERT FAIL: expected QUIC reject rule to be injected")
if not any(isinstance(item, dict) and item.get("ip_is_private") is True for item in rules):
    raise SystemExit("ASSERT FAIL: expected private ip direct rule to be injected")

outbounds = cfg.get("outbounds", [])
mapping = {item.get("tag"): item for item in outbounds if isinstance(item, dict)}
hk = mapping.get("HongKong", {})
if hk.get("default") != "A-HongKong":
    raise SystemExit("ASSERT FAIL: HongKong default should be A-HongKong")
if "A-HongKong" not in hk.get("outbounds", []) or "B-HongKong" not in hk.get("outbounds", []):
    raise SystemExit("ASSERT FAIL: HongKong should include A-HongKong and B-HongKong")
a_hk = mapping.get("A-HongKong", {})
if a_hk.get("type") != "urltest":
    raise SystemExit("ASSERT FAIL: expected A-HongKong to be urltest")

# Singapore/Japan should auto-pick the fastest node for each provider group by default.
b_sg = mapping.get("B-Singapore", {})
if b_sg.get("type") != "urltest":
    raise SystemExit("ASSERT FAIL: expected B-Singapore to be urltest")
a_jp = mapping.get("A-Japan", {})
if a_jp.get("type") != "urltest":
    raise SystemExit("ASSERT FAIL: expected A-Japan to be urltest")

# America remains a manual selector group (not urltest).
a_us = mapping.get("A-America", {})
if a_us.get("type") != "selector":
    raise SystemExit("ASSERT FAIL: expected A-America to remain selector")
proxy = mapping.get("Proxy", {})
if proxy.get("default") != "HongKong":
    raise SystemExit("ASSERT FAIL: Proxy default should follow group strategy default HongKong")
if "Streaming" not in proxy.get("outbounds", []) or "AI" not in proxy.get("outbounds", []):
    raise SystemExit("ASSERT FAIL: Proxy should include custom groups Streaming/AI")
PY

cat > "./build/qx-openai.list" <<'EOF'
DOMAIN-SUFFIX,openai.com
DOMAIN,chat.openai.com
DOMAIN-KEYWORD,chatgpt
IP-CIDR,1.1.1.1/32,no-resolve
EOF
cat > "./build/youtube.yaml" <<'EOF'
payload:
  - DOMAIN-SUFFIX,youtube.com
  - DOMAIN,music.youtube.com
  - DOMAIN-KEYWORD,youtube
EOF
cat > "./build/domains.txt" <<'EOF'
.example.org
example.net
EOF
cat > "./build/reject.list" <<'EOF'
DOMAIN-SUFFIX,ads.example
EOF
cat > "./config/rule-sources.json" <<'JSON'
{
  "final": "Proxy",
  "prepend_rules": [],
  "sources": [
    {
      "tag": "OpenAI",
      "enabled": true,
      "url": "./build/qx-openai.list",
      "outbound": "America"
    },
    {
      "tag": "YouTube",
      "enabled": true,
      "url": "./build/youtube.yaml",
      "outbound": "HongKong"
    },
    {
      "tag": "Custom",
      "enabled": true,
      "url": "./build/domains.txt",
      "outbound": "Singapore"
    },
    {
      "tag": "RejectSet",
      "enabled": true,
      "url": "./build/reject.list",
      "outbound": "Reject"
    }
  ],
  "manual_rules": [
    "DOMAIN-SUFFIX, ruc.edu.cn, Direct",
    "HOST, aistudio.google.com, America",
    "GEOIP, CN, Direct"
  ],
  "append_rules": []
}
JSON

./fly build-rules
assert_contains '"outbound": "America"' "./config/route-rules.json"
assert_contains '"outbound": "HongKong"' "./config/route-rules.json"
assert_contains '"outbound": "Singapore"' "./config/route-rules.json"
assert_contains '"outbound": "direct"' "./config/route-rules.json"
assert_contains '"outbound": "block"' "./config/route-rules.json"
assert_contains '"domain_suffix": \[' "./config/route-rules.json"
assert_contains '"domain": \[' "./config/route-rules.json"
assert_contains '"rule_set": \[' "./config/route-rules.json"
assert_contains '"geoip-cn"' "./config/route-rules.json"
assert_not_contains '"geoip": \[' "./config/route-rules.json"

./fly build-config
python3 - <<'PY'
import json

with open("./config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

rules = cfg.get("route", {}).get("rules", [])
if len(rules) < 7:
    raise SystemExit("ASSERT FAIL: expected generated route rules from build-rules + connectivity rules")
if not any(isinstance(item, dict) and item.get("action") == "hijack-dns" for item in rules):
    raise SystemExit("ASSERT FAIL: expected hijack-dns rule to be present")
if not any(
    isinstance(item, dict)
    and item.get("action") == "reject"
    and any(isinstance(rule, dict) and rule.get("protocol") == "quic" for rule in item.get("rules", []))
    for item in rules
):
    raise SystemExit("ASSERT FAIL: expected QUIC reject rule to be present")

tags = {item.get("tag") for item in cfg.get("outbounds", []) if isinstance(item, dict)}
if "block" not in tags:
    raise SystemExit("ASSERT FAIL: expected block outbound for Reject mapping")

route_sets = cfg.get("route", {}).get("rule_set", [])
if not any(isinstance(item, dict) and item.get("tag") == "geoip-cn" for item in route_sets):
    raise SystemExit("ASSERT FAIL: expected geoip-cn rule_set to be injected")
PY

./fly pipeline
assert_file_exists "./config.json"

cat > "./build/releases.json" <<'JSON'
[
  {
    "tag_name": "v1.13.0-rc.3",
    "prerelease": true,
    "assets": [
      {
        "name": "sing-box-1.13.0-rc.3-linux-amd64.tar.gz",
        "browser_download_url": "https://example.com/rc-linux-amd64.tar.gz"
      }
    ]
  },
  {
    "tag_name": "v1.12.20",
    "prerelease": false,
    "assets": [
      {
        "name": "sing-box-1.12.20-linux-amd64.tar.gz",
        "browser_download_url": "https://example.com/stable-linux-amd64.tar.gz"
      },
      {
        "name": "sing-box-1.12.20-darwin-arm64.tar.gz",
        "browser_download_url": "https://example.com/stable-darwin-arm64.tar.gz"
      }
    ]
  }
]
JSON

check_out="$(./fly check-singbox)"
if [[ "${check_out}" != installed_path=* ]]; then
  echo "ASSERT FAIL: expected installed path in check-singbox output, got '${check_out}'" >&2
  exit 1
fi
if ! printf '%s\n' "${check_out}" | grep -q "version=1.12.20"; then
  echo "ASSERT FAIL: expected version=1.12.20 in check-singbox output" >&2
  exit 1
fi

./fly install-singbox --dry-run --os linux --arch amd64 --version 1.12.20 --releases-json ./build/releases.json > "${WORK_DIR}/install.out"
assert_contains 'release_tag=v1.12.20' "${WORK_DIR}/install.out"
assert_contains 'stable-linux-amd64.tar.gz' "${WORK_DIR}/install.out"
assert_contains 'install_dir=\./bin-install' "${WORK_DIR}/install.out"
assert_contains 'will_skip=true' "${WORK_DIR}/install.out"

./fly install-guide --os darwin --arch arm64 --version latest --releases-json ./build/releases.json > "${WORK_DIR}/install-guide.out"
assert_contains 'stable-darwin-arm64.tar.gz' "${WORK_DIR}/install-guide.out"

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
