#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def validate_nodes(path: Path):
    data = load_json(path)
    if not isinstance(data, list) or not data:
        raise RuntimeError("extracted nodes must be a non-empty JSON array")
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise RuntimeError(f"node[{index}] must be an object")
        tag = item.get("tag")
        if not isinstance(tag, str) or not tag.strip():
            raise RuntimeError(f"node[{index}] missing valid tag")


def main():
    parser = argparse.ArgumentParser(description="Extract nodes only via sing-box-subscribe")
    parser.add_argument("--subscribe-dir", required=True, help="path to sing-box-subscribe directory")
    parser.add_argument("--providers-file", required=True, help="providers JSON used as extraction input")
    parser.add_argument("--output-file", required=True, help="nodes JSON output path")
    args = parser.parse_args()

    subscribe_dir = Path(args.subscribe_dir).resolve()
    providers_file = Path(args.providers_file).resolve()
    output_file = Path(args.output_file).resolve()
    main_py = subscribe_dir / "main.py"

    if not main_py.is_file():
        raise RuntimeError(f"missing sing-box-subscribe entry: {main_py}")
    if not providers_file.is_file():
        raise RuntimeError(f"missing providers file: {providers_file}")

    providers = load_json(providers_file)
    if not isinstance(providers, dict):
        raise RuntimeError("providers file must be a JSON object")

    payload = deepcopy(providers)
    payload["Only-nodes"] = True
    payload["save_config_path"] = str(output_file)

    cmd = [
        sys.executable,
        str(main_py),
        "--temp_json_data",
        json.dumps(payload, ensure_ascii=False),
    ]
    subprocess.run(cmd, cwd=str(subscribe_dir), check=True)
    validate_nodes(output_file)

    # Normalize output formatting for deterministic diffs.
    save_json(output_file, load_json(output_file))
    print(f"saved nodes: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
