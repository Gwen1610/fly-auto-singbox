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
assert_file_exists "./config/base-template.ios.json"

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
if [[ "${1:-}" == "rule-set" && "${2:-}" == "compile" ]]; then
  # Args: rule-set compile <in> -o <out>
  out=""
  for ((i=1; i<=$#; i++)); do
    arg="${!i}"
    if [[ "${arg}" == "-o" ]]; then
      j=$((i+1))
      out="${!j}"
      break
    fi
  done
  [[ -n "${out}" ]] || { echo "mock sing-box missing -o" >&2; exit 2; }
  mkdir -p "$(dirname "${out}")"
  printf 'dummy' > "${out}"
  exit 0
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
ROUTE_RULES_FILE_RULESET="./config/route-rules.ruleset.json"
BASE_TEMPLATE_FILE="./config/base-template.json"
BASE_TEMPLATE_FILE_IOS="./config/base-template.ios.json"
CONFIG_OUTPUT_DIR="./runtime-configs"
CONFIG_JSON="./runtime-configs/config.json"
CONFIG_JSON_IOS="./runtime-configs/config.ios.json"
CONFIG_JSON_TERMINAL="./runtime-configs/config.terminal.json"
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
assert_file_exists "./runtime-configs/config.json"
assert_contains '"tag": "Proxy"' "./runtime-configs/config.json"
assert_contains '"tag": "America"' "./runtime-configs/config.json"
assert_contains '"tag": "HongKong"' "./runtime-configs/config.json"
assert_contains '"tag": "A-HongKong"' "./runtime-configs/config.json"
assert_contains '"tag": "B-HongKong"' "./runtime-configs/config.json"
assert_contains '"tag": "Streaming"' "./runtime-configs/config.json"
assert_contains '"tag": "AI"' "./runtime-configs/config.json"
assert_not_contains 'geosite' "./runtime-configs/config.json"
assert_not_contains 'geoip' "./runtime-configs/config.json"
python3 - <<'PY'
import json

with open("./runtime-configs/config.json", "r", encoding="utf-8") as f:
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
      "tag": "ChinaRuleset",
      "enabled": true,
      "rule_set": [
        "geosite-cn",
        "geoip-cn"
      ],
      "outbound": "Direct"
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
    },
    {
      "tag": "广告",
      "enabled": true,
      "url": "./build/reject.list",
      "outbound": "Reject"
    },
    {
      "tag": "隐私",
      "enabled": true,
      "url": "./build/domains.txt",
      "outbound": "Singapore"
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
assert_contains '"geosite-cn"' "./config/route-rules.json"
assert_not_contains '"geoip": \[' "./config/route-rules.json"

./fly build-config
python3 - <<'PY'
import json

with open("./runtime-configs/config.json", "r", encoding="utf-8") as f:
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

# sing-box 1.11+ deprecates legacy special outbounds (e.g. `block`/`dns`) in route rules.
for item in rules:
    if not isinstance(item, dict):
        continue
    if item.get("outbound") in {"block", "dns"}:
        raise SystemExit("ASSERT FAIL: expected no legacy special outbounds in route rules")

tags = {item.get("tag") for item in cfg.get("outbounds", []) if isinstance(item, dict)}
if "dns_direct" not in tags:
    raise SystemExit("ASSERT FAIL: expected dns_direct outbound for VT-compatible DNS detour")
if "direct" in tags or "block" in tags:
    raise SystemExit("ASSERT FAIL: expected no legacy direct/block outbounds in final config")

route_sets = cfg.get("route", {}).get("rule_set", [])
if not any(isinstance(item, dict) and item.get("tag") == "geoip-cn" for item in route_sets):
    raise SystemExit("ASSERT FAIL: expected geoip-cn rule_set to be injected")
if not any(isinstance(item, dict) and item.get("tag") == "geosite-cn" for item in route_sets):
    raise SystemExit("ASSERT FAIL: expected geosite-cn rule_set to be injected")
PY

# Build rule-set files from QX sources and reference them by remote URLs (small config for iOS clients).
./fly build-rules --ruleset --base-url "https://example.com/ruleset" --ruleset-dir "./ruleset"
assert_file_exists "./ruleset/qx-openai.json"
assert_file_exists "./ruleset/qx-youtube.json"
assert_file_exists "./ruleset/qx-openai.srs"
assert_file_exists "./ruleset/qx-youtube.srs"

python3 - <<'PY'
import json

with open("./config/route-rules.ruleset.json", "r", encoding="utf-8") as f:
    rules_cfg = json.load(f)

route_sets = rules_cfg.get("rule_set", [])
if not isinstance(route_sets, list) or not route_sets:
    raise SystemExit("ASSERT FAIL: expected route-rules.json to include top-level rule_set list in ruleset mode")

by_tag = {item.get("tag"): item for item in route_sets if isinstance(item, dict)}
qx_tags = [item.get("tag") for item in route_sets if isinstance(item, dict) and str(item.get("tag", "")).startswith("qx-")]
qx_tags = [tag for tag in qx_tags if isinstance(tag, str)]
if len(qx_tags) != 6:
    raise SystemExit(f"ASSERT FAIL: expected 6 generated qx-* rule_set items, got {len(qx_tags)} ({qx_tags})")
if len(set(qx_tags)) != 6:
    raise SystemExit(f"ASSERT FAIL: expected generated qx-* rule_set tags to be unique, got {qx_tags}")
for tag in ("qx-openai", "qx-youtube", "qx-custom", "qx-rejectset"):
    item = by_tag.get(tag)
    if not item:
        raise SystemExit(f"ASSERT FAIL: missing rule_set definition for {tag}")
    if item.get("type") != "remote" or item.get("format") != "binary":
        raise SystemExit(f"ASSERT FAIL: unexpected rule_set definition for {tag}: {item}")
    if not str(item.get("url", "")).endswith(f"/{tag}.srs"):
        raise SystemExit(f"ASSERT FAIL: unexpected rule_set url for {tag}: {item.get('url')}")
    if item.get("download_detour") != "Proxy":
        raise SystemExit(f"ASSERT FAIL: expected download_detour=Proxy for {tag}")

rules = rules_cfg.get("rules", [])
if not any(isinstance(rule, dict) and rule.get("outbound") == "America" and rule.get("rule_set") == ["qx-openai"] for rule in rules):
    raise SystemExit("ASSERT FAIL: expected a qx-openai rule block for outbound America")
PY

./fly build-config --ruleset
python3 - <<'PY'
import json

with open("./runtime-configs/config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

route_sets = cfg.get("route", {}).get("rule_set", [])
tags = {item.get("tag") for item in route_sets if isinstance(item, dict)}
qx_tags = {tag for tag in tags if isinstance(tag, str) and tag.startswith("qx-")}
if len(qx_tags) != 6:
    raise SystemExit(f"ASSERT FAIL: expected 6 qx-* rule_set items in config.route.rule_set, got {len(qx_tags)} ({sorted(qx_tags)})")
for tag in ("qx-openai", "qx-youtube", "qx-custom", "qx-rejectset"):
    if tag not in tags:
        raise SystemExit(f"ASSERT FAIL: expected {tag} to be present in config.route.rule_set after build-ruleset")

route = cfg.get("route", {})
if isinstance(route, dict) and "default_domain_resolver" in route:
    raise SystemExit("ASSERT FAIL: desktop VT config should not include default_domain_resolver")

dns = cfg.get("dns")
servers = dns.get("servers", []) if isinstance(dns, dict) else []
if not any(isinstance(item, dict) and isinstance(item.get("address"), str) for item in servers):
    raise SystemExit("ASSERT FAIL: expected desktop VT config to use legacy dns address format")
if any(isinstance(item, dict) and "type" in item for item in servers):
    raise SystemExit("ASSERT FAIL: desktop VT config should not include dns.servers[].type")
server_by_tag = {item.get("tag"): item for item in servers if isinstance(item, dict)}
for tag in ("default-dns", "system-dns", "block-dns", "google"):
    if tag not in server_by_tag:
        raise SystemExit(f"ASSERT FAIL: expected dns server {tag} in desktop VT config")
tags_in_order = [item.get("tag") for item in servers if isinstance(item, dict)]
if "local" in tags_in_order:
    raise SystemExit("ASSERT FAIL: desktop Bulianglin DNS mode should remove legacy local DNS server")
if tags_in_order.index("default-dns") > tags_in_order.index("google"):
    raise SystemExit("ASSERT FAIL: default-dns must appear before google for address_resolver bootstrap")
if server_by_tag["default-dns"].get("detour") != "dns_direct":
    raise SystemExit("ASSERT FAIL: expected default-dns detour=dns_direct")
if server_by_tag["system-dns"].get("detour") != "dns_direct":
    raise SystemExit("ASSERT FAIL: expected system-dns detour=dns_direct")
if dns.get("final") != "google":
    raise SystemExit("ASSERT FAIL: expected desktop dns.final=google (Bulianglin style)")
if dns.get("strategy") != "ipv4_only":
    raise SystemExit("ASSERT FAIL: expected desktop dns.strategy=ipv4_only")

dns_rules = dns.get("rules", [])
if not any(isinstance(item, dict) and item.get("query_type") == "HTTPS" and item.get("server") == "block-dns" for item in dns_rules):
    raise SystemExit("ASSERT FAIL: expected dns rule query_type=HTTPS -> block-dns")
if not any(isinstance(item, dict) and item.get("outbound") == "any" and item.get("server") == "default-dns" for item in dns_rules):
    raise SystemExit("ASSERT FAIL: expected dns rule outbound=any -> default-dns")
if not any(isinstance(item, dict) and item.get("rule_set") in ("geosite-cn", "cnsite", "qx-china") and item.get("server") == "default-dns" for item in dns_rules):
    raise SystemExit("ASSERT FAIL: expected dns rule_set=cnsite/geosite-cn/qx-china -> default-dns")

route_rules = route.get("rules", [])
cn_direct_rules = [
    item for item in route_rules
    if isinstance(item, dict) and item.get("action") == "direct" and item.get("rule_set") == ["geosite-cn", "geoip-cn"]
]
if len(cn_direct_rules) != 1:
    raise SystemExit(f"ASSERT FAIL: expected exactly one CN direct route rule, got {len(cn_direct_rules)}")

# clash_api must be present in desktop config (for fly select/delay/monitor)
exp = cfg.get("experimental", {})
if "clash_api" not in exp:
    raise SystemExit("ASSERT FAIL: expected experimental.clash_api in desktop config.json")
if "external_controller" not in exp.get("clash_api", {}):
    raise SystemExit("ASSERT FAIL: expected experimental.clash_api.external_controller in desktop config.json")
PY

./fly build-config --ruleset --profile terminal
assert_file_exists "./runtime-configs/config.terminal.json"
python3 - <<'PY'
import json

with open("./runtime-configs/config.terminal.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

route = cfg.get("route", {})
if "default_domain_resolver" in route:
    raise SystemExit("ASSERT FAIL: terminal profile should avoid global route.default_domain_resolver to keep VT DNS behavior")

dns = cfg.get("dns", {})
servers = dns.get("servers", [])
server_by_tag = {item.get("tag"): item for item in servers if isinstance(item, dict)}
for tag in ("default-dns", "system-dns", "google"):
    if tag not in server_by_tag:
        raise SystemExit(f"ASSERT FAIL: expected terminal dns server {tag}")
if server_by_tag["default-dns"].get("type") != "udp":
    raise SystemExit("ASSERT FAIL: expected terminal default-dns type=udp")
if server_by_tag["google"].get("type") != "https":
    raise SystemExit("ASSERT FAIL: expected terminal google type=https")
if server_by_tag["google"].get("detour") != "Proxy":
    raise SystemExit("ASSERT FAIL: expected terminal google detour=Proxy to match VT anti-leak intent")
if server_by_tag["google"].get("domain_resolver") != "default-dns":
    raise SystemExit("ASSERT FAIL: expected terminal google server domain_resolver=default-dns for DoH bootstrap")
if "address" in server_by_tag["default-dns"]:
    raise SystemExit("ASSERT FAIL: expected terminal profile to avoid legacy dns address field on managed servers")
if server_by_tag["default-dns"].get("detour") in {"dns_direct", "direct"}:
    raise SystemExit("ASSERT FAIL: terminal default-dns should not detour to direct-type outbound (startup fatal in 1.12+)")

rules = dns.get("rules", [])
if any(isinstance(item, dict) and item.get("outbound") == "any" for item in rules):
    raise SystemExit("ASSERT FAIL: expected terminal profile dns.rules to avoid deprecated outbound=any item")
if not any(isinstance(item, dict) and item.get("query_type") == "HTTPS" and item.get("action") == "predefined" for item in rules):
    raise SystemExit("ASSERT FAIL: expected terminal profile query_type HTTPS predefined action rule")
if not any(isinstance(item, dict) and item.get("clash_mode") == "direct" and item.get("server") == "default-dns" for item in rules):
    raise SystemExit("ASSERT FAIL: expected terminal profile clash_mode=direct to use default-dns")
if any(isinstance(item, dict) and item.get("clash_mode") == "direct" and item.get("server") == "system-dns" for item in rules):
    raise SystemExit("ASSERT FAIL: terminal profile should not route clash_mode=direct to system-dns")

outbounds = cfg.get("outbounds", [])
dns_direct = next((item for item in outbounds if isinstance(item, dict) and item.get("tag") == "dns_direct"), None)
if not dns_direct:
    raise SystemExit("ASSERT FAIL: expected dns_direct outbound in terminal profile")
if dns_direct.get("domain_resolver") != "default-dns":
    raise SystemExit("ASSERT FAIL: expected dns_direct outbound domain_resolver=default-dns")

inbounds = cfg.get("inbounds", [])
tun_in = next((item for item in inbounds if isinstance(item, dict) and item.get("type") == "tun"), None)
if not tun_in:
    raise SystemExit("ASSERT FAIL: expected tun inbound in terminal profile")
if tun_in.get("sniff_override_destination") is not False:
    raise SystemExit("ASSERT FAIL: expected terminal tun sniff_override_destination=false (reduce DNS leak surfaces)")

route_rules = route.get("rules", [])
if not any(isinstance(item, dict) and item.get("action") == "hijack-dns" for item in route_rules):
    raise SystemExit("ASSERT FAIL: expected terminal profile to keep hijack-dns rule")
if not any(
    isinstance(item, dict)
    and item.get("action") == "reject"
    and any(isinstance(rule, dict) and rule.get("protocol") == "quic" for rule in item.get("rules", []))
    for item in route_rules
):
    raise SystemExit("ASSERT FAIL: expected terminal profile to keep QUIC reject rule")
if not any(isinstance(item, dict) and item.get("action") == "resolve" and item.get("inbound") == "mixed-in" for item in route_rules):
    raise SystemExit("ASSERT FAIL: expected terminal profile to add mixed-in resolve rule (avoid system DNS leaks in proxy mode)")

cn_direct_rules = [
    item for item in route_rules
    if isinstance(item, dict) and item.get("action") == "direct" and item.get("rule_set") == ["geosite-cn", "geoip-cn"]
]
if len(cn_direct_rules) != 1:
    raise SystemExit(f"ASSERT FAIL: expected terminal profile to keep one CN direct route rule, got {len(cn_direct_rules)}")
PY

# Simulate a user-modified iOS template that accidentally contains new DNS schema fields.
python3 - <<'PY'
import json

path = "./config/base-template.ios.json"
with open(path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

cfg.setdefault("dns", {})
cfg["dns"]["servers"] = [
    {"tag": "legacy-bad", "type": "https", "server": "1.1.1.1", "detour": "direct"},
]
cfg.setdefault("route", {})
cfg["route"]["default_domain_resolver"] = "legacy-bad"

with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
    f.write("\n")
PY

./fly build-config --target ios --ruleset
assert_file_exists "./runtime-configs/config.ios.json"
python3 - <<'PY'
import json

with open("./runtime-configs/config.ios.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

inbounds = cfg.get("inbounds", [])
types = [item.get("type") for item in inbounds if isinstance(item, dict)]
if "tun" not in types:
    raise SystemExit("ASSERT FAIL: expected iOS config to include tun inbound")
if "mixed" in types:
    raise SystemExit("ASSERT FAIL: iOS config should not include mixed inbound by default")

dns = cfg.get("dns")
if not isinstance(dns, dict) or not dns.get("servers"):
    raise SystemExit("ASSERT FAIL: expected iOS config to include dns.servers (VT 1.11.4 friendly)")

servers = dns.get("servers", [])
if not any(isinstance(item, dict) and isinstance(item.get("address"), str) for item in servers):
    raise SystemExit("ASSERT FAIL: expected iOS dns.servers to use legacy address format (no type/server)")
if any(isinstance(item, dict) and "type" in item for item in servers):
    raise SystemExit("ASSERT FAIL: iOS dns.servers should not include 'type' field (VT 1.11.4 decode failure)")
server_by_tag = {item.get("tag"): item for item in servers if isinstance(item, dict)}
for tag in ("default-dns", "system-dns", "block-dns", "google"):
    if tag not in server_by_tag:
        raise SystemExit(f"ASSERT FAIL: expected dns server {tag} in iOS VT config")
tags_in_order = [item.get("tag") for item in servers if isinstance(item, dict)]
if "local" in tags_in_order:
    raise SystemExit("ASSERT FAIL: iOS Bulianglin DNS mode should remove legacy local DNS server")
if tags_in_order.index("default-dns") > tags_in_order.index("google"):
    raise SystemExit("ASSERT FAIL: iOS default-dns must appear before google for address_resolver bootstrap")
if server_by_tag["default-dns"].get("detour") != "dns_direct":
    raise SystemExit("ASSERT FAIL: expected iOS default-dns detour=dns_direct")
if server_by_tag["system-dns"].get("detour") != "dns_direct":
    raise SystemExit("ASSERT FAIL: expected iOS system-dns detour=dns_direct")
if dns.get("final") != "google":
    raise SystemExit("ASSERT FAIL: expected iOS dns.final=google (Bulianglin style)")

route = cfg.get("route", {})
if isinstance(route, dict) and "default_domain_resolver" in route:
    raise SystemExit("ASSERT FAIL: iOS route should not include default_domain_resolver (VT 1.11.4 decode failure)")
rules = route.get("rules", []) if isinstance(route, dict) else []
if not any(
    isinstance(item, dict)
    and item.get("action") == "reject"
    and any(isinstance(rule, dict) and rule.get("protocol") == "quic" for rule in item.get("rules", []))
    for item in rules
):
    raise SystemExit("ASSERT FAIL: expected iOS VT config to include QUIC reject logical rule")
dns_rules = dns.get("rules", [])
if not any(isinstance(item, dict) and item.get("query_type") == "HTTPS" and item.get("server") == "block-dns" for item in dns_rules):
    raise SystemExit("ASSERT FAIL: expected iOS dns rule query_type=HTTPS -> block-dns")
if not any(isinstance(item, dict) and item.get("outbound") == "any" and item.get("server") == "default-dns" for item in dns_rules):
    raise SystemExit("ASSERT FAIL: expected iOS dns rule outbound=any -> default-dns")
if not any(isinstance(item, dict) and item.get("rule_set") in ("geosite-cn", "cnsite", "qx-china") and item.get("server") == "default-dns" for item in dns_rules):
    raise SystemExit("ASSERT FAIL: expected iOS dns rule_set=cnsite/geosite-cn/qx-china -> default-dns")

cn_direct_rules = [
    item for item in rules
    if isinstance(item, dict) and item.get("action") == "direct" and item.get("rule_set") == ["geosite-cn", "geoip-cn"]
]
if len(cn_direct_rules) != 1:
    raise SystemExit(f"ASSERT FAIL: expected exactly one iOS CN direct route rule, got {len(cn_direct_rules)}")

# iOS config must NOT contain clash_api (not needed on device, VT 1.11.4 doesn't use it)
ios_exp = cfg.get("experimental", {})
if "clash_api" in ios_exp:
    raise SystemExit("ASSERT FAIL: iOS config should not contain experimental.clash_api")
PY

mkdir -p "./ruleset"
echo "dummy" > "./ruleset/dummy.srs"
pub_out="$(./fly publish-ruleset --dry-run)"
if ! printf '%s\n' "${pub_out}" | grep -q "staged_changes=true"; then
  echo "ASSERT FAIL: expected staged_changes=true in publish-ruleset output, got:" >&2
  printf '%s\n' "${pub_out}" >&2
  exit 1
fi

./fly pipeline
assert_file_exists "./runtime-configs/config.json"

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

cp "./runtime-configs/config.terminal.json" "./runtime-configs/custom.profile.json"
./fly on --config custom.profile.json
assert_file_exists "./.sing-box.pid"
pid_before="$(cat ./.sing-box.pid)"
status_out="$(./fly status)"
if [[ "${status_out}" != running* ]]; then
  echo "ASSERT FAIL: expected running status, got '${status_out}'" >&2
  exit 1
fi

on_again="$(./fly on --config custom.profile.json)"
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

cat > "./sing-box.log" <<'EOF'
INFO[0000] hello
WARN[0001] warn
ERROR[0002] error
EOF
filtered_warn="$(./fly log --no-follow -n 50 --level warn)"
if ! printf '%s\n' "${filtered_warn}" | grep -q '^WARN\['; then
  echo "ASSERT FAIL: expected WARN lines in filtered warn output, got '${filtered_warn}'" >&2
  exit 1
fi
if ! printf '%s\n' "${filtered_warn}" | grep -q '^ERROR\['; then
  echo "ASSERT FAIL: expected ERROR lines in filtered warn output, got '${filtered_warn}'" >&2
  exit 1
fi
if printf '%s\n' "${filtered_warn}" | grep -q '^INFO\['; then
  echo "ASSERT FAIL: INFO should be filtered out at level=warn, got '${filtered_warn}'" >&2
  exit 1
fi

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
