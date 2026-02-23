#!/usr/bin/env python3
import argparse
import json
import re
import sys
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path

URLTEST_REGIONS = {"HongKong", "Singapore", "Japan"}
URLTEST_URL = "https://www.gstatic.com/generate_204"
URLTEST_INTERVAL = "10m"

GOOGLE_DNS_SUFFIXES = [
    "google.com",
    "gstatic.com",
    "googleapis.com",
    "googlevideo.com",
    "1e100.net",
    "youtube.com",
    "ytimg.com",
    "ggpht.com",
    "github.com",
    "githubusercontent.com",
]

REGION_PATTERNS = OrderedDict(
    [
        (
            "America",
            re.compile(
                r"(🇺🇸|🇺🇲|美国|美國|美西|美东|美東|洛杉矶|洛杉磯|纽约|紐約|旧金山|舊金山|"
                r"United\s*States|\bUSA?\b|America|US\d+)",
                re.IGNORECASE,
            ),
        ),
        (
            "HongKong",
            re.compile(
                r"(🇭🇰|香港|港线|港線|Hong\s*Kong|HongKong|\bHK\b|HK\d+|\bHKT\b|\bHKBN\b|\bHGC\b|\bWTT\b|\bCMI\b|HKG)",
                re.IGNORECASE,
            ),
        ),
        (
            "Singapore",
            re.compile(r"(🇸🇬|新加坡|狮城|獅城|Singapore|\bSG\b|SG\d+|SGP)", re.IGNORECASE),
        ),
        (
            "Japan",
            re.compile(r"(🇯🇵|日本|东京|東京|大阪|Japan|\bJP\b|JP\d+|JPN)", re.IGNORECASE),
        ),
    ]
)

REGION_ALIASES = {
    "america": "America",
    "us": "America",
    "usa": "America",
    "hongkong": "HongKong",
    "hk": "HongKong",
    "singapore": "Singapore",
    "sg": "Singapore",
    "japan": "Japan",
    "jp": "Japan",
}

OUTBOUND_ALIAS = {
    "proxy": "Proxy",
    "america": "America",
    "us": "America",
    "usa": "America",
    "hongkong": "HongKong",
    "hong_kong": "HongKong",
    "hk": "HongKong",
    "singapore": "Singapore",
    "sg": "Singapore",
    "japan": "Japan",
    "jp": "Japan",
    "direct": "direct",
    "reject": "block",
    "block": "block",
}

GEOIP_TAG_RE = re.compile(r"^[a-z0-9-]+$", re.IGNORECASE)


def guess_ruleset_remote_url(tag: str) -> str:
    """
    Return an official SagerNet rule-set URL for a tag.

    Notes:
    - sing-box `route.rule_set` uses `.srs` binaries from:
      - https://github.com/SagerNet/sing-geosite/tree/rule-set
      - https://github.com/SagerNet/sing-geoip/tree/rule-set
    - Common tag patterns:
      - geoip-<cc> (e.g. geoip-cn)
      - geosite-<name> (e.g. geosite-openai)
      - category-<name> (e.g. category-ads-all) maps to geosite-category-<name>.srs
    """
    text = str(tag).strip()
    if not text:
        return ""

    if text.startswith("geoip-"):
        repo = "sing-geoip"
        filename = text
    elif text.startswith("geosite-"):
        repo = "sing-geosite"
        filename = text
    elif text.startswith("category-"):
        repo = "sing-geosite"
        filename = f"geosite-{text}"
    else:
        return ""

    return f"https://raw.githubusercontent.com/SagerNet/{repo}/rule-set/{filename}.srs"


def make_ruleset_preset(tag: str):
    url = guess_ruleset_remote_url(tag)
    if not url:
        return None
    return {
        "tag": tag,
        "type": "remote",
        "format": "binary",
        "url": url,
        # For iOS / CN networks, GitHub raw is often slow/blocked on direct.
        # Using Proxy makes rule-set initialization significantly more reliable.
        "download_detour": "Proxy",
    }


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def dedupe_nodes(nodes):
    seen = set()
    deduped = []
    for node in nodes:
        tag = node.get("tag")
        if tag in seen:
            continue
        deduped.append(node)
        seen.add(tag)
    return deduped


def validate_nodes(nodes):
    if not isinstance(nodes, list) or not nodes:
        raise RuntimeError("nodes file must be a non-empty JSON array")
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise RuntimeError(f"nodes[{index}] must be object")
        tag = node.get("tag")
        if not isinstance(tag, str) or not tag.strip():
            raise RuntimeError(f"nodes[{index}] missing tag")


def normalize_region_name(raw):
    value = str(raw).strip()
    if not value:
        return value
    compact = re.sub(r"[^a-z]", "", value.lower())
    if compact in REGION_ALIASES:
        return REGION_ALIASES[compact]
    return value


def detect_region(tag):
    for region, pattern in REGION_PATTERNS.items():
        if pattern.search(tag):
            return region
    return None


def group_nodes_by_region_and_provider(nodes):
    grouped = OrderedDict((region, OrderedDict()) for region in REGION_PATTERNS.keys())
    total = 0
    for node in nodes:
        region = detect_region(node.get("tag", ""))
        if not region:
            continue
        provider = str(node.get("__provider_tag", "default")).strip() or "default"
        grouped[region].setdefault(provider, []).append(node)
        total += 1
    if total == 0:
        raise RuntimeError("no America/HongKong/Singapore/Japan nodes found")
    return grouped


def normalize_outbound(raw):
    if raw is None:
        return raw
    value = str(raw).strip()
    if not value:
        return value
    return OUTBOUND_ALIAS.get(value.lower(), value)


def strip_internal_fields(node):
    output = {}
    for key, value in node.items():
        if str(key).startswith("__"):
            continue
        output[key] = value
    return output


def make_provider_region_tag(provider, region):
    return f"{provider}-{region}"


def resolve_selector_member(raw, available_tags):
    if not isinstance(raw, str):
        return ""
    value = raw.strip()
    if not value:
        return ""

    normalized_region = normalize_region_name(value)
    if normalized_region in available_tags:
        return normalized_region
    if value in available_tags:
        return value
    for tag in available_tags:
        if str(tag).lower() == value.lower():
            return tag
    return ""


def resolve_region_default(region, members, preferred):
    if not members:
        return "direct"
    if not preferred:
        return members[0]

    pref = str(preferred).strip()
    if not pref:
        return members[0]
    if pref in members:
        return pref

    candidate = make_provider_region_tag(pref, region)
    if candidate in members:
        return candidate

    for item in members:
        if item.lower() == pref.lower() or item.lower() == candidate.lower():
            return item
    return members[0]


def load_group_strategy(path: Path):
    cfg = load_json(path)
    if not isinstance(cfg, dict):
        raise RuntimeError("group strategy file must be a JSON object")

    region_defaults_raw = cfg.get("region_defaults", {})
    custom_groups_raw = cfg.get("custom_groups", [])
    proxy_raw = cfg.get("proxy", {})

    if not isinstance(region_defaults_raw, dict):
        raise RuntimeError("group strategy region_defaults must be object")
    if not isinstance(custom_groups_raw, list):
        raise RuntimeError("group strategy custom_groups must be array")
    if not isinstance(proxy_raw, dict):
        raise RuntimeError("group strategy proxy must be object")

    region_defaults = {}
    for key, value in region_defaults_raw.items():
        region_key = normalize_region_name(key)
        region_defaults[region_key] = str(value).strip()

    custom_groups = []
    for index, item in enumerate(custom_groups_raw):
        if not isinstance(item, dict):
            raise RuntimeError(f"custom_groups[{index}] must be object")
        tag = str(item.get("tag", "")).strip()
        members = item.get("members", [])
        default = str(item.get("default", "")).strip()
        if not tag:
            raise RuntimeError(f"custom_groups[{index}].tag must be non-empty string")
        if not isinstance(members, list):
            raise RuntimeError(f"custom_groups[{index}].members must be array")
        custom_groups.append({"tag": tag, "members": members, "default": default})

    proxy_members = proxy_raw.get("members", list(REGION_PATTERNS.keys()))
    proxy_default = str(proxy_raw.get("default", "Proxy")).strip()
    if not isinstance(proxy_members, list):
        raise RuntimeError("group strategy proxy.members must be array")

    return {
        "region_defaults": region_defaults,
        "custom_groups": custom_groups,
        "proxy": {"members": proxy_members, "default": proxy_default},
    }


def is_ip_address(value: str) -> bool:
    # Good enough for our config use: v4 literal or anything containing ':' treated as IP (v6).
    text = str(value).strip()
    if not text:
        return False
    if ":" in text:
        return True
    return bool(re.match(r"^\d+\.\d+\.\d+\.\d+$", text))


def guess_domain_suffix(hostname: str) -> str:
    text = str(hostname).strip().strip(".").lower()
    if not text or is_ip_address(text) or "." not in text:
        return ""
    labels = [part for part in text.split(".") if part]
    if len(labels) < 2:
        return ""
    tld = labels[-1]
    sld = labels[-2]
    if len(tld) == 2 and sld in {"com", "net", "org", "gov", "edu", "co"} and len(labels) >= 3:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def collect_node_domain_suffixes(outbounds):
    suffixes = set()
    for item in outbounds:
        if not isinstance(item, dict):
            continue
        server = item.get("server")
        if not isinstance(server, str):
            continue
        suffix = guess_domain_suffix(server)
        if suffix:
            suffixes.add(suffix)
    return sorted(suffixes)


def ensure_inbound_sniff(config):
    inbounds = config.get("inbounds", [])
    if not isinstance(inbounds, list):
        return
    for inbound in inbounds:
        if not isinstance(inbound, dict):
            continue
        if inbound.get("type") not in {"tun", "mixed"}:
            continue
        inbound.setdefault("sniff", True)
        inbound.setdefault("sniff_override_destination", True)


def upsert_dns_server(servers, tag: str, desired: dict):
    for item in servers:
        if isinstance(item, dict) and item.get("tag") == tag:
            item.clear()
            item.update(deepcopy(desired))
            return
    servers.append(deepcopy(desired))


def ensure_connectivity_dns(config, outbounds):
    dns = config.get("dns")
    if not isinstance(dns, dict):
        dns = {}
        config["dns"] = dns

    servers = dns.get("servers")
    if not isinstance(servers, list):
        servers = []
        dns["servers"] = servers

    legacy = any(isinstance(item, dict) and "address" in item for item in servers)

    google_server = (
        {"tag": "google", "address": "tls://8.8.8.8", "detour": "Proxy"}
        if legacy
        else {"tag": "google", "type": "tls", "server": "8.8.8.8", "detour": "Proxy"}
    )
    local_server = (
        {"tag": "local", "address": "https://223.5.5.5/dns-query", "detour": "direct"}
        if legacy
        else {"tag": "local", "type": "https", "server": "223.5.5.5", "detour": "direct"}
    )

    upsert_dns_server(
        servers,
        "google",
        google_server,
    )
    upsert_dns_server(servers, "local", local_server)

    dns.setdefault("final", "local")
    dns.setdefault("strategy", "ipv4_only")

    rules = dns.get("rules")
    if not isinstance(rules, list):
        rules = []
        dns["rules"] = rules

    node_suffixes = collect_node_domain_suffixes(outbounds)
    prefix_rules = []

    if node_suffixes:
        prefix_rules.append(
            {
                "type": "logical",
                "mode": "or",
                "rules": [{"domain_suffix": suffix} for suffix in node_suffixes],
                "server": "local",
            }
        )
    prefix_rules.append(
        {
            "type": "logical",
            "mode": "or",
            "rules": [{"domain_suffix": suffix} for suffix in GOOGLE_DNS_SUFFIXES],
            "server": "google",
        }
    )

    # Avoid repeatedly injecting when users run build-config multiple times.
    existing = json.dumps(rules, ensure_ascii=False, sort_keys=True)
    inject = []
    for item in prefix_rules:
        if json.dumps(item, ensure_ascii=False, sort_keys=True) not in existing:
            inject.append(item)

    if inject:
        dns["rules"] = [*inject, *rules]


def ensure_connectivity_dns_ios(config, outbounds):
    dns = config.get("dns")
    if not isinstance(dns, dict):
        dns = {}
        config["dns"] = dns

    servers = dns.get("servers")
    if not isinstance(servers, list):
        servers = []
        dns["servers"] = servers

    # Keep legacy DNS server format for better VT (1.11.x) compatibility.
    upsert_dns_server(
        servers,
        "local",
        {"tag": "local", "address": "https://223.5.5.5/dns-query", "detour": "direct"},
    )
    upsert_dns_server(
        servers,
        "google",
        {"tag": "google", "address": "tls://8.8.8.8", "detour": "Proxy"},
    )

    dns.setdefault("final", "local")
    dns.setdefault("strategy", "ipv4_only")

    rules = dns.get("rules")
    if not isinstance(rules, list):
        rules = []
        dns["rules"] = rules

    node_suffixes = collect_node_domain_suffixes(outbounds)
    prefix_rules = []

    if node_suffixes:
        prefix_rules.append({"domain_suffix": node_suffixes, "server": "local"})
    prefix_rules.append({"domain_suffix": GOOGLE_DNS_SUFFIXES, "server": "google"})

    existing = json.dumps(rules, ensure_ascii=False, sort_keys=True)
    inject = []
    for item in prefix_rules:
        if json.dumps(item, ensure_ascii=False, sort_keys=True) not in existing:
            inject.append(item)

    if inject:
        dns["rules"] = [*inject, *rules]


def ensure_connectivity_route(config, user_rules):
    route = config.get("route")
    if not isinstance(route, dict):
        route = {}
        config["route"] = route

    # NOTE: Do not inject `default_domain_resolver` by default.
    # Older sing-box cores (e.g. 1.11.x) don't know this field and will fail to decode config.

    base_rules = [
        {
            "type": "logical",
            "mode": "or",
            "rules": [{"protocol": "dns"}, {"port": 53}],
            "action": "hijack-dns",
        },
        {
            "type": "logical",
            "mode": "or",
            "rules": [{"protocol": "quic"}, {"network": "udp", "port": 443}],
            "action": "reject",
        },
        {"ip_is_private": True, "outbound": "direct"},
    ]

    combined = []
    existing = json.dumps(user_rules, ensure_ascii=False, sort_keys=True)
    for item in base_rules:
        if json.dumps(item, ensure_ascii=False, sort_keys=True) not in existing:
            combined.append(item)
    combined.extend(user_rules)
    return combined


def ensure_connectivity_route_ios(user_rules):
    # iOS sing-box VT (core 1.11.x) tends to be more fragile with complex logical rule blocks.
    # Keep a conservative, minimal rule set close to "quickstart" configs.
    base_rules = [
        {"protocol": "dns", "action": "hijack-dns"},
        {"ip_is_private": True, "outbound": "direct"},
    ]
    combined = []
    existing = json.dumps(user_rules, ensure_ascii=False, sort_keys=True)
    for item in base_rules:
        if json.dumps(item, ensure_ascii=False, sort_keys=True) not in existing:
            combined.append(item)
    combined.extend(user_rules)
    return combined


def build_outbounds(grouped, strategy):
    selectors = []
    node_outbounds = []
    available_selector_tags = set()
    region_tags = []
    custom_tags = []

    for region in REGION_PATTERNS.keys():
        provider_groups = []
        for provider, nodes in grouped[region].items():
            node_tags = [item.get("tag") for item in nodes if isinstance(item.get("tag"), str)]
            if not node_tags:
                continue

            source_region_tag = make_provider_region_tag(provider, region)
            if region in URLTEST_REGIONS:
                selectors.append(
                    {
                        "tag": source_region_tag,
                        "type": "urltest",
                        "outbounds": node_tags,
                        "url": URLTEST_URL,
                        "interval": URLTEST_INTERVAL,
                    }
                )
            else:
                selectors.append(
                    {
                        "tag": source_region_tag,
                        "type": "selector",
                        "outbounds": node_tags,
                        "default": node_tags[0],
                    }
                )
            available_selector_tags.add(source_region_tag)
            provider_groups.append(source_region_tag)
            node_outbounds.extend(strip_internal_fields(node) for node in nodes)

        if provider_groups:
            region_default = resolve_region_default(
                region,
                provider_groups,
                strategy["region_defaults"].get(region, ""),
            )
            members = provider_groups
        else:
            region_default = "direct"
            members = ["direct"]

        selectors.append(
            {"tag": region, "type": "selector", "outbounds": members, "default": region_default}
        )
        available_selector_tags.add(region)
        region_tags.append(region)

    for group in strategy["custom_groups"]:
        members = []
        for raw_member in group["members"]:
            resolved = resolve_selector_member(raw_member, available_selector_tags)
            if resolved and resolved not in members:
                members.append(resolved)
        if not members:
            continue

        default_member = resolve_selector_member(group["default"], set(members))
        if not default_member:
            default_member = members[0]
        selectors.append(
            {
                "tag": group["tag"],
                "type": "selector",
                "outbounds": members,
                "default": default_member,
            }
        )
        available_selector_tags.add(group["tag"])
        custom_tags.append(group["tag"])

    proxy_members = []
    for raw_member in strategy["proxy"]["members"]:
        resolved = resolve_selector_member(raw_member, available_selector_tags)
        if resolved and resolved not in proxy_members:
            proxy_members.append(resolved)
    if not proxy_members:
        proxy_members = [*region_tags, *custom_tags] or ["direct"]

    proxy_default = resolve_selector_member(strategy["proxy"]["default"], set(proxy_members))
    if not proxy_default:
        proxy_default = proxy_members[0]

    outbounds = [
        {
            "tag": "Proxy",
            "type": "selector",
            "outbounds": proxy_members,
            "default": proxy_default,
        },
        *selectors,
        {"type": "direct", "tag": "direct"},
        {"type": "block", "tag": "block"},
        *node_outbounds,
    ]
    return outbounds


def ensure_legacy_geoip_compat(rule):
    if "geoip" not in rule:
        return
    value = rule.pop("geoip")
    values = value if isinstance(value, list) else [value]
    normalized = [str(item).strip().lower() for item in values if str(item).strip()]
    if not normalized:
        return
    existing = rule.get("rule_set", [])
    if isinstance(existing, str):
        existing = [existing]
    if not isinstance(existing, list):
        raise RuntimeError("rule_set must be string or array when converting geoip")
    for item in normalized:
        if not GEOIP_TAG_RE.match(item):
            raise RuntimeError(f"geoip matcher value not supported: {item}")
        tag = f"geoip-{item}"
        if tag not in existing:
            existing.append(tag)
    rule["rule_set"] = existing


def collect_required_rule_sets(rules):
    tags = set()
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        value = rule.get("rule_set")
        if isinstance(value, str):
            tags.add(value)
        elif isinstance(value, list):
            tags.update(str(item) for item in value)
    return tags


def validate_rules(rules_cfg, outbound_tags):
    if not isinstance(rules_cfg, dict):
        raise RuntimeError("rules file must be a JSON object")
    rules = rules_cfg.get("rules", [])
    final = normalize_outbound(rules_cfg.get("final", "Proxy"))
    if not isinstance(rules, list):
        raise RuntimeError("rules must be an array")
    if final not in outbound_tags:
        raise RuntimeError(f"route final outbound not found: {final}")
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise RuntimeError(f"rules[{index}] must be object")
        ensure_legacy_geoip_compat(rule)
        outbound = normalize_outbound(rule.get("outbound"))
        if "outbound" in rule:
            rule["outbound"] = outbound
        if outbound and outbound not in outbound_tags:
            raise RuntimeError(f"rules[{index}] outbound not found: {outbound}")
    return final, rules


def build_config(base_template, outbounds, final_outbound, rules, extra_rule_sets=None, target="desktop"):
    config = deepcopy(base_template)
    if "inbounds" not in config:
        raise RuntimeError("base template must contain inbounds")

    route_base = config.get("route", {})
    if not isinstance(route_base, dict):
        route_base = {}
    existing_rule_sets = route_base.get("rule_set", [])
    if isinstance(existing_rule_sets, dict):
        existing_rule_sets = [existing_rule_sets]
    if not isinstance(existing_rule_sets, list):
        existing_rule_sets = []

    existing_tags = set()
    for item in existing_rule_sets:
        if isinstance(item, dict) and isinstance(item.get("tag"), str):
            existing_tags.add(item["tag"])

    if isinstance(extra_rule_sets, dict):
        extra_rule_sets = [extra_rule_sets]
    if isinstance(extra_rule_sets, list):
        for item in extra_rule_sets:
            if not isinstance(item, dict):
                continue
            tag = item.get("tag")
            if not isinstance(tag, str) or not tag.strip():
                continue
            if tag in existing_tags:
                continue
            existing_rule_sets.append(deepcopy(item))
            existing_tags.add(tag)

    for tag in sorted(collect_required_rule_sets(rules)):
        if tag in existing_tags:
            continue
        preset = make_ruleset_preset(tag)
        if preset is None:
            continue
        existing_rule_sets.append(deepcopy(preset))
        existing_tags.add(tag)

    route_base["final"] = final_outbound
    if str(target).strip().lower() == "ios":
        route_base["rules"] = ensure_connectivity_route_ios(rules)
    else:
        route_base["rules"] = ensure_connectivity_route(config, rules)
    route_base["rule_set"] = existing_rule_sets

    config["outbounds"] = outbounds
    config["route"] = route_base
    ensure_inbound_sniff(config)
    if str(target).strip().lower() == "ios":
        ensure_connectivity_dns_ios(config, outbounds)
    else:
        ensure_connectivity_dns(config, outbounds)
    return config


def main():
    parser = argparse.ArgumentParser(description="Build final sing-box config from nodes + rules + groups")
    parser.add_argument("--nodes-file", required=True)
    parser.add_argument("--rules-file", required=True)
    parser.add_argument("--groups-file", required=True)
    parser.add_argument("--template-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--target", choices=["desktop", "ios"], default="desktop")
    args = parser.parse_args()

    nodes = load_json(Path(args.nodes_file).resolve())
    validate_nodes(nodes)
    nodes = dedupe_nodes(nodes)

    grouped = group_nodes_by_region_and_provider(nodes)
    groups_cfg = load_group_strategy(Path(args.groups_file).resolve())
    outbounds = build_outbounds(grouped, groups_cfg)
    outbound_tags = {item.get("tag") for item in outbounds if isinstance(item, dict)}

    rules_cfg = load_json(Path(args.rules_file).resolve())
    extra_rule_sets = rules_cfg.get("rule_set")
    final_outbound, rules = validate_rules(rules_cfg, outbound_tags)

    base_template = load_json(Path(args.template_file).resolve())
    config = build_config(
        base_template,
        outbounds,
        final_outbound,
        rules,
        extra_rule_sets=extra_rule_sets,
        target=args.target,
    )
    output_path = Path(args.output_file).resolve()

    def estimate_route_items(route: dict) -> int:
        total = 0
        rules = route.get("rules", [])
        if isinstance(rules, list):
            keys = {
                "domain_suffix",
                "domain",
                "domain_keyword",
                "domain_regex",
                "ip_cidr",
                "source_ip_cidr",
                "port",
                "source_port",
                "rule_set",
            }
            for rule in rules:
                if not isinstance(rule, dict):
                    continue
                for key in keys:
                    value = rule.get(key)
                    if isinstance(value, list):
                        total += len(value)
                    elif isinstance(value, str) and value:
                        total += 1
        rule_sets = route.get("rule_set", [])
        if isinstance(rule_sets, list):
            total += len(rule_sets)
        return total

    # Auto-compact huge config for iOS clients that may time out / crash on very large JSON with indentation.
    estimated_items = estimate_route_items(config.get("route", {}))
    compact = estimated_items >= 20000
    if compact:
        print(f"info: compact_json=true (estimated_items={estimated_items})", file=sys.stderr)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        if compact:
            json.dump(config, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")

    region_counts = {region: sum(len(items) for items in grouped[region].values()) for region in grouped}
    print(f"region counts: {region_counts}")
    print(f"saved config: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
