# QX Rule Conversion Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `fly-auto-singbox` 中新增一个独立模块，把 QX/Clash 规则源转换成 sing-box 可用的 `config/route-rules.json`。

**Architecture:** 新增 `scripts/build_route_rules.py`，只负责读取规则源配置并生成 `route-rules.json`，不耦合节点提取和配置构建。`fly` 新增 `build-rules` 命令，`build-config` 继续消费 `route-rules.json`。

**Tech Stack:** Bash (`fly`), Python 3 (`requests`, `PyYAML`, `ipaddress`), JSON 配置文件。

### Task 1: Define Source Config + Command Surface

**Files:**
- Modify: `fly-auto-singbox/fly`
- Create: `fly-auto-singbox/config/rule-sources.example.json`
- Modify: `fly-auto-singbox/config/fly.env.example`
- Modify: `fly-auto-singbox/.gitignore`

**Steps:**
1. 新增 `RULE_SOURCES_FILE` 环境变量与默认路径。
2. `./fly init` 生成 `config/rule-sources.json`（由 example 复制）。
3. 新增 `./fly build-rules` 命令：读取 rule sources 并输出 `route-rules.json`。

### Task 2: Implement Converter Module

**Files:**
- Create: `fly-auto-singbox/scripts/build_route_rules.py`

**Steps:**
1. 支持读取 URL/本地文件的 `.list/.yaml/.txt` 规则源。
2. 实现常见 QX/Clash 规则映射到 sing-box 字段（domain/domain_suffix/domain_keyword/ip_cidr 等）。
3. 按 source 的 `outbound` 聚合生成规则对象，最终产出 `{final, rules}` 到 `route-rules.json`。

### Task 3: Tests and Docs

**Files:**
- Modify: `fly-auto-singbox/tests/test_pipeline.sh`
- Modify: `fly-auto-singbox/README.md`

**Steps:**
1. 测试中构造本地 `.list/.yaml/.txt` 样例，执行 `./fly build-rules`。
2. 断言生成的 `route-rules.json` 包含预期字段与 `outbound`，并被 `build-config` 正常消费。
3. README 增加规则转换使用说明，并注明 `sing-box-geosite` 原作者与仓库链接。
