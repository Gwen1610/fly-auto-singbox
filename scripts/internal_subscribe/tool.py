import base64
import random
import re
import string
import urllib.parse

REGION_PATTERNS = {
    "America": re.compile(
        r"(🇺🇸|美国|美國|洛杉矶|洛杉磯|纽约|紐約|旧金山|舊金山|United\\s*States|\\bUSA?\\b|America)",
        re.IGNORECASE,
    ),
    "HongKong": re.compile(r"(🇭🇰|香港|Hong\\s*Kong|\\bHK\\b)", re.IGNORECASE),
    "Singapore": re.compile(r"(🇸🇬|新加坡|狮城|獅城|Singapore|\\bSG\\b)", re.IGNORECASE),
    "Japan": re.compile(r"(🇯🇵|日本|东京|東京|大阪|Japan|\\bJP\\b)", re.IGNORECASE),
}

REGION_EMOJI = {
    "America": "🇺🇸",
    "HongKong": "🇭🇰",
    "Singapore": "🇸🇬",
    "Japan": "🇯🇵",
}


def b64Decode(value: str) -> bytes:
    raw = urllib.parse.unquote(value.strip())
    padding = (-len(raw)) % 4
    raw = raw + ("=" * padding)
    return base64.urlsafe_b64decode(raw.encode("utf-8"))


def noblankLine(data: str) -> str:
    return "\n".join(line.strip() for line in data.splitlines() if line.strip())


def genName(length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def get_protocol(uri: str):
    try:
        match = re.search(r"^(.+?)://", uri)
    except Exception:
        return None
    if not match:
        return None
    proto = match.group(1)
    if proto == "hy2":
        proto = "hysteria2"
    elif proto == "wireguard":
        proto = "wg"
    elif proto == "http2":
        proto = "http"
    elif proto == "socks5":
        proto = "socks"
    return proto


def rename(name: str) -> str:
    if not isinstance(name, str):
        return name
    stripped = name.strip()
    for region, pattern in REGION_PATTERNS.items():
        if pattern.search(stripped):
            emoji = REGION_EMOJI[region]
            if stripped.startswith(emoji):
                return stripped
            return f"{emoji} {stripped}"
    return stripped


def proDuplicateNodeName(grouped_nodes):
    # grouped_nodes: dict[tag_group, list[node]]
    seen = {}
    for _, nodes in grouped_nodes.items():
        for node in nodes:
            name = str(node.get("tag", "")).strip()
            if not name:
                continue
            count = seen.get(name, 0)
            if count == 0:
                seen[name] = 1
                continue
            new_name = f"{name}-{count + 1}"
            while new_name in seen:
                count += 1
                new_name = f"{name}-{count + 1}"
            node["tag"] = new_name
            seen[name] = count + 1
            seen[new_name] = 1
