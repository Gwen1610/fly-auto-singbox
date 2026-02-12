#!/usr/bin/env python3
import argparse
import json
import re
import sys
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path

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

RULE_SET_PRESETS = {
    "geoip-cn": {
        "tag": "geoip-cn",
        "type": "remote",
        "format": "binary",
        "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@sing/geo/geoip/cn.srs",
        "download_detour": "direct",
    }
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


def detect_region(tag):
    for region, pattern in REGION_PATTERNS.items():
        if pattern.search(tag):
            return region
    return None


def group_nodes(nodes):
    grouped = OrderedDict((name, []) for name in REGION_PATTERNS.keys())
    for node in nodes:
        region = detect_region(node.get("tag", ""))
        if region:
            grouped[region].append(node)
    total = sum(len(items) for items in grouped.values())
    if total == 0:
        raise RuntimeError("no America/HongKong/Singapore/Japan nodes found")
    return grouped


def build_outbounds(grouped):
    outbounds = [
        {
            "tag": "Proxy",
            "type": "selector",
            "outbounds": ["America", "HongKong", "Singapore", "Japan"],
            "default": "America",
        }
    ]
    for region in ("America", "HongKong", "Singapore", "Japan"):
        members = [item["tag"] for item in grouped.get(region, [])]
        if not members:
            members = ["direct"]
        outbounds.append({"tag": region, "type": "selector", "outbounds": members})
    outbounds.append({"type": "direct", "tag": "direct"})
    outbounds.append({"type": "block", "tag": "block"})

    for region in grouped:
        outbounds.extend(grouped[region])
    return outbounds


def normalize_outbound(raw):
    if raw is None:
        return raw
    value = str(raw).strip()
    if not value:
        return value
    return OUTBOUND_ALIAS.get(value.lower(), value)


def ensure_legacy_geoip_compat(rule):
    if "geoip" not in rule:
        return
    value = rule.pop("geoip")
    values = value if isinstance(value, list) else [value]
    normalized = [str(item).strip().lower() for item in values if str(item).strip()]
    if not normalized:
        return
    unsupported = [item for item in normalized if item != "cn"]
    if unsupported:
        raise RuntimeError(
            "geoip matcher is removed in sing-box 1.12; unsupported geoip values: "
            + ",".join(unsupported)
        )
    existing = rule.get("rule_set", [])
    if isinstance(existing, str):
        existing = [existing]
    if not isinstance(existing, list):
        raise RuntimeError("rule_set must be string or array when converting geoip")
    if "geoip-cn" not in existing:
        existing.append("geoip-cn")
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


def build_config(base_template, outbounds, final_outbound, rules):
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

    for tag in sorted(collect_required_rule_sets(rules)):
        preset = RULE_SET_PRESETS.get(tag)
        if preset and tag not in existing_tags:
            existing_rule_sets.append(deepcopy(preset))
            existing_tags.add(tag)

    route_base["final"] = final_outbound
    route_base["rules"] = rules
    route_base["rule_set"] = existing_rule_sets

    config["outbounds"] = outbounds
    config["route"] = route_base
    return config


def main():
    parser = argparse.ArgumentParser(description="Build final sing-box config from nodes + rules")
    parser.add_argument("--nodes-file", required=True)
    parser.add_argument("--rules-file", required=True)
    parser.add_argument("--template-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    nodes = load_json(Path(args.nodes_file).resolve())
    validate_nodes(nodes)
    nodes = dedupe_nodes(nodes)

    grouped = group_nodes(nodes)
    outbounds = build_outbounds(grouped)
    outbound_tags = {item.get("tag") for item in outbounds if isinstance(item, dict)}

    rules_cfg = load_json(Path(args.rules_file).resolve())
    final_outbound, rules = validate_rules(rules_cfg, outbound_tags)

    base_template = load_json(Path(args.template_file).resolve())
    config = build_config(base_template, outbounds, final_outbound, rules)
    save_json(Path(args.output_file).resolve(), config)

    region_counts = {k: len(v) for k, v in grouped.items()}
    print(f"region counts: {region_counts}")
    print(f"saved config: {Path(args.output_file).resolve()}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
