#!/usr/bin/env python3
import argparse
import ipaddress
import json
import hashlib
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

try:
    import requests  # type: ignore
except Exception:
    requests = None

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

MAP_DICT = {
    "DOMAIN-SUFFIX": "domain_suffix",
    "HOST-SUFFIX": "domain_suffix",
    "host-suffix": "domain_suffix",
    "DOMAIN": "domain",
    "HOST": "domain",
    "host": "domain",
    "DOMAIN-KEYWORD": "domain_keyword",
    "HOST-KEYWORD": "domain_keyword",
    "host-keyword": "domain_keyword",
    "IP-CIDR": "ip_cidr",
    "ip-cidr": "ip_cidr",
    "IP-CIDR6": "ip_cidr",
    "IP6-CIDR": "ip_cidr",
    "SRC-IP-CIDR": "source_ip_cidr",
    "DST-PORT": "port",
    "SRC-PORT": "source_port",
    "URL-REGEX": "domain_regex",
    "DOMAIN-REGEX": "domain_regex",
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


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def read_text_from_source(source: str, base_dir: Path) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        if requests is not None:
            resp = requests.get(source, timeout=30)
            resp.raise_for_status()
            return resp.text
        req = urllib.request.Request(source, headers={"User-Agent": "fly-auto-singbox/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    file_path = Path(source)
    if not file_path.is_absolute():
        candidate_from_cfg = (base_dir / file_path).resolve()
        if candidate_from_cfg.exists():
            file_path = candidate_from_cfg
        else:
            file_path = (Path.cwd() / file_path).resolve()
    return file_path.read_text(encoding="utf-8")


def is_ip_network(text: str) -> bool:
    try:
        ipaddress.ip_network(text, strict=False)
        return True
    except ValueError:
        return False


def normalize_raw_value(raw: str) -> str:
    value = raw.strip().strip("'").strip('"').strip()
    if not value:
        return ""
    if value.startswith("+.") or value.startswith("*."):
        value = value[2:]
    elif value.startswith("."):
        value = value[1:]
    return value.strip()


def parse_entry(raw: str) -> Tuple[str, str]:
    line = raw.strip()
    if not line:
        return "", ""
    if line.startswith("#") or line.startswith(";") or line.startswith("//"):
        return "", ""
    if line.upper().startswith("AND,") or line.upper().startswith("OR,") or line.upper().startswith("NOT,"):
        # Keep the first version simple: skip logical rules.
        return "", ""

    if "," in line:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            return "", ""
        pattern = parts[0]
        value = normalize_raw_value(parts[1])
        if not value:
            return "", ""
        if pattern.upper() == "GEOIP":
            # sing-box 1.12 removed legacy geoip matcher; map to rule-set tag.
            # Example: GEOIP,CN -> rule_set=geoip-cn
            code = value.lower()
            if not code or not code.replace("-", "").isalnum():
                raise RuntimeError(f"GEOIP value not supported: {value}")
            return "rule_set", f"geoip-{code}"
        key = MAP_DICT.get(pattern)
        if not key:
            return "", ""
        return key, value

    value = normalize_raw_value(line)
    if not value:
        return "", ""
    if is_ip_network(value):
        return "ip_cidr", value
    if raw.strip().startswith("+.") or raw.strip().startswith("."):
        return "domain_suffix", value
    return "domain", value


def normalize_outbound(raw: str) -> str:
    value = str(raw).strip()
    if not value:
        return value
    return OUTBOUND_ALIAS.get(value.lower(), value)


def parse_manual_rule_line(raw: str) -> Tuple[str, str, str]:
    line = raw.strip()
    if not line or line.startswith("#") or line.startswith(";") or line.startswith("//"):
        return "", "", ""
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 3:
        raise RuntimeError(f"manual rule requires at least 3 fields: {raw}")

    key, value = parse_entry(",".join(parts[:2]))
    if not key or not value:
        raise RuntimeError(f"manual rule pattern not supported: {raw}")

    outbound = normalize_outbound(parts[2])
    if not outbound:
        raise RuntimeError(f"manual rule outbound is empty: {raw}")
    return key, value, outbound


def normalize_rule_outbounds(rules: List[dict]) -> List[dict]:
    normalized: List[dict] = []
    for rule in rules:
        if not isinstance(rule, dict):
            normalized.append(rule)
            continue
        copied = dict(rule)
        if isinstance(copied.get("outbound"), str):
            copied["outbound"] = normalize_outbound(copied["outbound"])
        normalized.append(copied)
    return normalized


def slugify_tag(text: str) -> str:
    value = str(text).strip().lower()
    if not value:
        return "ruleset"
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "ruleset"


def parse_entries_from_yaml(text: str) -> Iterable[str]:
    if yaml is None:
        # Minimal fallback parser for payload-based yaml when PyYAML is unavailable.
        lines = text.splitlines()
        in_payload = False
        items: List[str] = []
        for raw in lines:
            line = raw.rstrip()
            stripped = line.strip()
            if stripped.startswith("payload:"):
                in_payload = True
                continue
            if not in_payload:
                continue
            if stripped.startswith("- "):
                items.append(stripped[2:].strip().strip('"').strip("'"))
            elif stripped and not stripped.startswith("#"):
                break
        return items or lines

    try:
        data = yaml.safe_load(text)
    except Exception:
        return text.splitlines()

    if isinstance(data, dict) and isinstance(data.get("payload"), list):
        return [str(item) for item in data["payload"]]
    if isinstance(data, list):
        return [str(item) for item in data]
    return text.splitlines()


def parse_source_rules(source: str, content: str) -> Dict[str, Set[str]]:
    values_by_key: Dict[str, Set[str]] = {}
    lowered = source.lower()
    if lowered.endswith(".yaml") or lowered.endswith(".yml"):
        entries = parse_entries_from_yaml(content)
    else:
        entries = content.splitlines()

    for entry in entries:
        key, value = parse_entry(str(entry))
        if not key or not value:
            continue
        values_by_key.setdefault(key, set()).add(value)
    return values_by_key


def validate_source_item(item: dict, index: int):
    if not isinstance(item, dict):
        raise RuntimeError(f"sources[{index}] must be an object")
    if not isinstance(item.get("enabled", False), bool):
        raise RuntimeError(f"sources[{index}].enabled must be boolean")
    if not isinstance(item.get("outbound", ""), str) or not item.get("outbound", "").strip():
        raise RuntimeError(f"sources[{index}].outbound must be non-empty string")
    url = item.get("url")
    rule_set = item.get("rule_set")
    has_url = isinstance(url, str) and url.strip()
    if isinstance(rule_set, str):
        has_rule_set = bool(rule_set.strip())
    elif isinstance(rule_set, list):
        has_rule_set = any(str(value).strip() for value in rule_set)
    else:
        has_rule_set = False
    if not has_url and not has_rule_set:
        raise RuntimeError(f"sources[{index}] requires either non-empty url or rule_set")


def normalize_rule_set_value(raw) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        value = raw.strip()
        return [value] if value else []
    if isinstance(raw, list):
        items: List[str] = []
        for item in raw:
            text = str(item).strip()
            if text and text not in items:
                items.append(text)
        return items
    return []


def main():
    parser = argparse.ArgumentParser(description="Build config/route-rules.json from QX/Clash rule sources")
    parser.add_argument("--sources-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument(
        "--mode",
        choices=["inline", "ruleset"],
        default="inline",
        help="inline: expand QX rules into route.rules; ruleset: compile QX rules into .srs and reference via rule_set tags",
    )
    parser.add_argument(
        "--ruleset-dir",
        default="./ruleset",
        help="Directory to write compiled rule-set files when mode=ruleset",
    )
    parser.add_argument(
        "--ruleset-base-url",
        default="",
        help="Base URL for raw .srs files (e.g. https://raw.githubusercontent.com/<user>/<repo>/main/ruleset) when mode=ruleset",
    )
    parser.add_argument(
        "--ruleset-download-detour",
        default="Proxy",
        help="download_detour to use in route.rule_set remote items when mode=ruleset",
    )
    parser.add_argument(
        "--ruleset-tag-prefix",
        default="qx-",
        help="Prefix for generated rule_set tags when mode=ruleset",
    )
    parser.add_argument(
        "--sing-box-bin",
        default="sing-box",
        help="sing-box binary to use for `rule-set compile` when mode=ruleset",
    )
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Skip compiling .json to .srs (useful for tests). Still emits route-rules.json referencing .srs by URL.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON (no indentation). Useful when some clients are slow or crash on large configs.",
    )
    args = parser.parse_args()

    sources_path = Path(args.sources_file).resolve()
    cfg = load_json(sources_path)
    if not isinstance(cfg, dict):
        raise RuntimeError("rule sources file must be a JSON object")

    final = cfg.get("final", "Proxy")
    prepend_rules = cfg.get("prepend_rules", [])
    append_rules = cfg.get("append_rules", [])
    manual_rules = cfg.get("manual_rules", [])
    sources = cfg.get("sources", [])

    if not isinstance(final, str) or not final.strip():
        raise RuntimeError("final must be non-empty string")
    if not isinstance(prepend_rules, list):
        raise RuntimeError("prepend_rules must be array")
    if not isinstance(append_rules, list):
        raise RuntimeError("append_rules must be array")
    if not isinstance(manual_rules, list):
        raise RuntimeError("manual_rules must be array")
    if not isinstance(sources, list):
        raise RuntimeError("sources must be array")
    for index, item in enumerate(manual_rules):
        if not isinstance(item, str):
            raise RuntimeError(f"manual_rules[{index}] must be string")

    final = normalize_outbound(final)
    prepend_rules = normalize_rule_outbounds(prepend_rules)
    append_rules = normalize_rule_outbounds(append_rules)

    built_rules: List[dict] = []
    route_rule_sets: List[dict] = []
    enabled_count = 0
    used_ruleset_tags: Set[str] = set()

    mode = str(args.mode).strip().lower()
    ruleset_dir = Path(args.ruleset_dir).resolve()
    ruleset_base_url = str(args.ruleset_base_url).strip().rstrip("/")
    ruleset_download_detour = str(args.ruleset_download_detour).strip() or "Proxy"
    ruleset_tag_prefix = str(args.ruleset_tag_prefix)
    sing_box_bin = str(args.sing_box_bin).strip() or "sing-box"

    if mode == "ruleset":
        if not ruleset_base_url:
            raise RuntimeError("--ruleset-base-url is required when --mode=ruleset")
        ruleset_dir.mkdir(parents=True, exist_ok=True)

    for index, item in enumerate(sources):
        validate_source_item(item, index)
        if not item.get("enabled", False):
            continue

        enabled_count += 1
        outbound = normalize_outbound(item["outbound"].strip())
        tag = str(item.get("tag", f"source-{index + 1}"))

        rule_sets = normalize_rule_set_value(item.get("rule_set"))
        if rule_sets:
            built_rules.append({"rule_set": rule_sets, "outbound": outbound})
            print(f"source '{tag}' -> rule_set={rule_sets}", file=sys.stderr)
            continue

        src = str(item.get("url", "")).strip()
        text = read_text_from_source(src, sources_path.parent)
        values_by_key = parse_source_rules(src, text)
        if not values_by_key:
            print(f"warn: source '{tag}' produced no usable rules, skip", file=sys.stderr)
            continue

        if mode == "inline":
            rule = {key: sorted(values) for key, values in sorted(values_by_key.items())}
            rule["outbound"] = outbound
            built_rules.append(rule)
            print(
                f"source '{tag}' -> {sum(len(v) for v in values_by_key.values())} entries",
                file=sys.stderr,
            )
            continue

        slug = slugify_tag(tag)
        if slug == "ruleset":
            fingerprint = hashlib.sha1(f"{tag}|{src}|{outbound}".encode("utf-8", errors="ignore")).hexdigest()[:8]
            slug = slugify_tag(f"source-{fingerprint}")
        ruleset_tag = f"{ruleset_tag_prefix}{slug}"
        if ruleset_tag in used_ruleset_tags:
            suffix = 2
            while f"{ruleset_tag}-{suffix}" in used_ruleset_tags:
                suffix += 1
            ruleset_tag = f"{ruleset_tag}-{suffix}"
        used_ruleset_tags.add(ruleset_tag)
        json_path = (ruleset_dir / f"{ruleset_tag}.json").resolve()
        srs_path = (ruleset_dir / f"{ruleset_tag}.srs").resolve()

        ruleset_json = {
            "version": 1,
            "rules": [{key: sorted(values) for key, values in sorted(values_by_key.items())}],
        }
        json_path.write_text(json.dumps(ruleset_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        if not args.skip_compile:
            try:
                subprocess.run(
                    [sing_box_bin, "rule-set", "compile", str(json_path), "-o", str(srs_path)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
            except FileNotFoundError as exc:
                raise RuntimeError(f"cannot run sing-box: {sing_box_bin}") from exc
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f"sing-box rule-set compile failed for {json_path}") from exc

        built_rules.append({"rule_set": [ruleset_tag], "outbound": outbound})
        route_rule_sets.append(
            {
                "tag": ruleset_tag,
                "type": "remote",
                "format": "binary",
                "url": f"{ruleset_base_url}/{ruleset_tag}.srs",
                "download_detour": ruleset_download_detour,
            }
        )
        print(
            f"source '{tag}' -> ruleset_tag={ruleset_tag} entries={sum(len(v) for v in values_by_key.values())}",
            file=sys.stderr,
        )

    if enabled_count == 0:
        print("warn: no enabled rule sources; output will keep only prepend/append rules", file=sys.stderr)

    manual_map: Dict[Tuple[str, str], Set[str]] = {}
    for line in manual_rules:
        key, value, outbound = parse_manual_rule_line(line)
        if not key:
            continue
        manual_map.setdefault((outbound, key), set()).add(value)

    manual_blocks: List[dict] = []
    for (outbound, key), values in sorted(manual_map.items(), key=lambda x: (x[0][0], x[0][1])):
        manual_blocks.append({key: sorted(values), "outbound": outbound})

    output = {"final": final, "rules": [*prepend_rules, *built_rules, *manual_blocks, *append_rules]}
    if route_rule_sets:
        output["rule_set"] = route_rule_sets

    output_path = Path(args.output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        if args.compact:
            json.dump(output, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"saved route rules: {Path(args.output_file).resolve()}")
    print(f"generated rule blocks: {len(built_rules) + len(manual_blocks)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
