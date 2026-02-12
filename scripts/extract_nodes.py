#!/usr/bin/env python3
import argparse
import base64
import json
import os
import re
import sys
import time
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    requests = None

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

from internal_subscribe import tool
from internal_subscribe.parsers import (
    anytls,
    http,
    https,
    hysteria,
    hysteria2,
    socks,
    ss,
    ssr,
    trojan,
    tuic,
    vless,
    vmess,
    wg,
)
from internal_subscribe.parsers.clash2base64 import clash2v2ray

SHARE_PREFIXES = (
    "vmess://",
    "vless://",
    "ss://",
    "ssr://",
    "trojan://",
    "tuic://",
    "hysteria://",
    "hysteria2://",
    "hy2://",
    "wg://",
    "wireguard://",
    "http2://",
    "http://",
    "https://",
    "socks://",
    "socks5://",
    "anytls://",
)

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
            re.compile(r"(🇭🇰|香港|港线|港線|Hong\s*Kong|HongKong|\bHK\b|HK\d+|\bHKT\b|\bHKBN\b|\bHGC\b|\bWTT\b|\bCMI\b|HKG)", re.IGNORECASE),
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

PARSERS = {
    "vmess": vmess.parse,
    "vless": vless.parse,
    "ss": ss.parse,
    "ssr": ssr.parse,
    "trojan": trojan.parse,
    "tuic": tuic.parse,
    "hysteria": hysteria.parse,
    "hysteria2": hysteria2.parse,
    "wg": wg.parse,
    "http": http.parse,
    "https": https.parse,
    "socks": socks.parse,
    "anytls": anytls.parse,
}


def parse_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_content(content: str):
    nodes = []
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        proto = tool.get_protocol(line)
        parser_fn = PARSERS.get(proto or "")
        if not parser_fn:
            continue
        try:
            parsed = parser_fn(line)
        except Exception:
            continue
        if not parsed:
            continue
        if isinstance(parsed, tuple):
            nodes.extend(item for item in parsed if item)
        else:
            nodes.append(parsed)
    return nodes


def maybe_decode_base64(text: str):
    compact = "".join(text.split())
    if not compact:
        return None
    if not re.fullmatch(r"[A-Za-z0-9+/=]+", compact):
        return None
    try:
        return base64.b64decode(compact, validate=True).decode("utf-8", errors="ignore")
    except Exception:
        return None


def get_content_from_url(url: str, user_agent: str = "", retries: int = 3):
    if url.startswith(SHARE_PREFIXES):
        return tool.noblankLine(url)

    user_agent = user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    response_text = None
    for attempt in range(1, retries + 1):
        try:
            if requests is not None:
                response = requests.get(url, headers={"User-Agent": user_agent}, timeout=30)
                if response.status_code == 200:
                    try:
                        response_text = response.content.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        response_text = response.text
                    break
            else:
                request = Request(url, headers={"User-Agent": user_agent})
                with urlopen(request, timeout=30) as response:  # nosec
                    raw = response.read()
                response_text = raw.decode("utf-8-sig", errors="ignore")
                break
        except Exception:
            response_text = None
        if attempt < retries:
            time.sleep(1)

    if response_text is None:
        return None
    response_text = response_text or ""
    if not response_text.strip():
        return None

    if response_text.startswith(SHARE_PREFIXES):
        return tool.noblankLine(response_text)

    loaded_yaml = None
    if yaml is not None:
        try:
            loaded_yaml = yaml.safe_load(response_text.replace("\t", " "))
        except Exception:
            loaded_yaml = None
    if isinstance(loaded_yaml, dict) and "proxies" in loaded_yaml:
        return loaded_yaml

    try:
        loaded_json = json.loads(re.sub(r"//.*", "", response_text))
    except json.JSONDecodeError:
        loaded_json = None
    if isinstance(loaded_json, dict) and "outbounds" in loaded_json:
        return loaded_json

    decoded = maybe_decode_base64(response_text)
    if decoded:
        return decoded
    return response_text


def get_content_from_file(path: str):
    file_path = Path(path)
    raw = file_path.read_bytes()
    ext = file_path.suffix.lower()
    if ext in {".yaml", ".yml"} and yaml is not None:
        parsed_yaml = yaml.safe_load(raw)
        if isinstance(parsed_yaml, dict) and "proxies" in parsed_yaml:
            links = [clash2v2ray(proxy) for proxy in parsed_yaml["proxies"]]
            return "\n".join(link for link in links if link)
    return tool.noblankLine(raw.decode("utf-8", errors="ignore"))


def extract_nodes_from_content(content):
    if isinstance(content, dict):
        if "proxies" in content:
            links = [clash2v2ray(proxy) for proxy in content["proxies"]]
            return parse_content("\n".join(link for link in links if link))
        if "outbounds" in content:
            excluded_types = {"selector", "urltest", "direct", "block", "dns"}
            return [
                item
                for item in content["outbounds"]
                if isinstance(item, dict) and item.get("type") not in excluded_types and item.get("tag")
            ]
        return []
    return parse_content(str(content))


def get_nodes(raw_source: str, user_agent: str = ""):
    source = raw_source.strip()
    if not source:
        return []

    if source.startswith("sub://"):
        source = tool.b64Decode(source[6:]).decode("utf-8", errors="ignore")

    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        return extract_nodes_from_content(get_content_from_url(source, user_agent=user_agent))
    if parsed.scheme in {item.split("://")[0] for item in SHARE_PREFIXES}:
        return parse_content(source)
    if os.path.exists(source):
        return extract_nodes_from_content(get_content_from_file(source))

    decoded = maybe_decode_base64(source)
    if decoded:
        return parse_content(decoded)
    return parse_content(source)


def apply_subscribe_transforms(nodes, subscribe_cfg):
    prefix = str(subscribe_cfg.get("prefix", "")).strip()
    use_emoji = bool(subscribe_cfg.get("emoji"))
    excludes = [item.strip() for item in re.split(r"[,\|]", str(subscribe_cfg.get("ex-node-name", ""))) if item.strip()]

    transformed = []
    for node in nodes:
        tag = str(node.get("tag", "")).strip()
        if not tag:
            continue
        if excludes and any(block in tag for block in excludes):
            continue

        item = dict(node)
        if prefix:
            item["tag"] = f"{prefix}{item['tag']}"
            if item.get("detour"):
                item["detour"] = f"{prefix}{item['detour']}"
        if use_emoji:
            item["tag"] = tool.rename(item["tag"])
            if item.get("detour"):
                item["detour"] = tool.rename(item["detour"])
        transformed.append(item)
    return transformed


def detect_region(tag: str):
    for region, pattern in REGION_PATTERNS.items():
        if pattern.search(tag):
            return region
    return None


def filter_nodes_by_region(nodes):
    grouped = OrderedDict((region, []) for region in REGION_PATTERNS.keys())
    unmatched_tags = []
    for node in nodes:
        tag = str(node.get("tag", ""))
        region = detect_region(tag)
        if region:
            grouped[region].append(node)
        else:
            unmatched_tags.append(tag)

    total = sum(len(items) for items in grouped.values())
    if total == 0:
        uniq = []
        seen = set()
        for tag in unmatched_tags:
            if tag in seen:
                continue
            seen.add(tag)
            uniq.append(tag)
            if len(uniq) >= 8:
                break
        sample = ", ".join(uniq) if uniq else "<none>"
        raise RuntimeError(
            "no US/HK/SG/JP nodes found after filtering; sample tags: "
            + sample
            + ". check node naming or set prefix in config/extract.providers.json"
        )

    output = []
    for region in grouped:
        output.extend(grouped[region])
    counts = {region: len(grouped[region]) for region in grouped}
    return output, counts


def process_subscribes(subscribes):
    grouped = {}
    for subscribe in subscribes:
        if not subscribe.get("enabled", True):
            continue
        raw_source = str(subscribe.get("url", "")).strip()
        if not raw_source:
            continue
        nodes = get_nodes(raw_source, user_agent=str(subscribe.get("User-Agent", "")))
        if not nodes:
            continue
        nodes = apply_subscribe_transforms(nodes, subscribe)
        if not nodes:
            continue

        tag = str(subscribe.get("tag", "default")).strip() or "default"
        subgroup = str(subscribe.get("subgroup", "")).strip()
        if subgroup:
            tag = f"{tag}-{subgroup}-subgroup"
        grouped.setdefault(tag, []).extend(nodes)

    tool.proDuplicateNodeName(grouped)
    flattened = []
    for key in grouped:
        flattened.extend(grouped[key])
    return flattened


def validate_output(nodes):
    if not isinstance(nodes, list) or not nodes:
        raise RuntimeError("extracted nodes must be a non-empty array")
    for idx, item in enumerate(nodes):
        if not isinstance(item, dict):
            raise RuntimeError(f"node[{idx}] must be object")
        tag = item.get("tag")
        if not isinstance(tag, str) or not tag.strip():
            raise RuntimeError(f"node[{idx}] missing valid tag")


def main():
    parser = argparse.ArgumentParser(description="Extract US/HK/SG/JP nodes (no route rules)")
    parser.add_argument("--providers-file", required=True, help="providers JSON path")
    parser.add_argument("--output-file", required=True, help="nodes output path")
    args = parser.parse_args()

    providers_file = Path(args.providers_file).resolve()
    output_file = Path(args.output_file).resolve()
    if not providers_file.is_file():
        raise RuntimeError(f"missing providers file: {providers_file}")

    providers = parse_json(providers_file)
    if not isinstance(providers, dict):
        raise RuntimeError("providers file must be a JSON object")

    subscribes = providers.get("subscribes", [])
    if not isinstance(subscribes, list):
        raise RuntimeError("providers.subscribes must be an array")

    nodes = process_subscribes(subscribes)
    nodes, counts = filter_nodes_by_region(nodes)
    validate_output(nodes)
    write_json(output_file, nodes)
    print(f"region counts: {counts}")
    print(f"saved nodes: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
