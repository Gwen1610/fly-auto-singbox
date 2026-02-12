#!/usr/bin/env python3
import argparse
import ipaddress
import json
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
    "GEOIP": "geoip",
    "DST-PORT": "port",
    "SRC-PORT": "source_port",
    "URL-REGEX": "domain_regex",
    "DOMAIN-REGEX": "domain_regex",
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
    if not isinstance(item.get("url", ""), str) or not item.get("url", "").strip():
        raise RuntimeError(f"sources[{index}].url must be non-empty string")
    if not isinstance(item.get("outbound", ""), str) or not item.get("outbound", "").strip():
        raise RuntimeError(f"sources[{index}].outbound must be non-empty string")


def main():
    parser = argparse.ArgumentParser(description="Build config/route-rules.json from QX/Clash rule sources")
    parser.add_argument("--sources-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    sources_path = Path(args.sources_file).resolve()
    cfg = load_json(sources_path)
    if not isinstance(cfg, dict):
        raise RuntimeError("rule sources file must be a JSON object")

    final = cfg.get("final", "Proxy")
    prepend_rules = cfg.get("prepend_rules", [])
    append_rules = cfg.get("append_rules", [])
    sources = cfg.get("sources", [])

    if not isinstance(final, str) or not final.strip():
        raise RuntimeError("final must be non-empty string")
    if not isinstance(prepend_rules, list):
        raise RuntimeError("prepend_rules must be array")
    if not isinstance(append_rules, list):
        raise RuntimeError("append_rules must be array")
    if not isinstance(sources, list):
        raise RuntimeError("sources must be array")

    built_rules: List[dict] = []
    enabled_count = 0
    for index, item in enumerate(sources):
        validate_source_item(item, index)
        if not item.get("enabled", False):
            continue

        enabled_count += 1
        src = item["url"].strip()
        outbound = item["outbound"].strip()
        tag = str(item.get("tag", f"source-{index + 1}"))

        text = read_text_from_source(src, sources_path.parent)
        values_by_key = parse_source_rules(src, text)
        if not values_by_key:
            print(f"warn: source '{tag}' produced no usable rules, skip", file=sys.stderr)
            continue

        rule = {key: sorted(values) for key, values in sorted(values_by_key.items())}
        rule["outbound"] = outbound
        built_rules.append(rule)
        print(f"source '{tag}' -> {sum(len(v) for v in values_by_key.values())} entries", file=sys.stderr)

    if enabled_count == 0:
        print("warn: no enabled rule sources; output will keep only prepend/append rules", file=sys.stderr)

    output = {"final": final, "rules": [*prepend_rules, *built_rules, *append_rules]}
    save_json(Path(args.output_file).resolve(), output)
    print(f"saved route rules: {Path(args.output_file).resolve()}")
    print(f"generated rule blocks: {len(built_rules)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
