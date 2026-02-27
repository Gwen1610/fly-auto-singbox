# Terminal DNS Leak Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate “terminal 模式 DNS 泄露”问题（以 macOS 为主），同时保持 VT 档（1.11.4）不回退，并尽量避免 1.12+ 的 deprecated warn。

**Architecture:** 采用“配置层 + 运行期 guard”双保险：terminal profile 在路由层对 `mixed-in` 注入 `resolve`，避免代理模式走系统 DNS；运行期在 macOS 上对系统 DNS 做临时 guard（含 IPv6），以覆盖“系统 DNS 来自 LAN/IPv6 resolver 绕过 tun”的常见漏点。

**Tech Stack:** Bash（`fly`）、Python（`scripts/build_config.py`）、sing-box（terminal core 1.12+）。

---

### Task 1: 复盘泄露入口并确定修复点

**Files:**
- Review: `docs/bulianglin-dns-leak-borrowing-notes.md`
- Review: `scripts/build_config.py`
- Review: `fly`
- Review: `findings.md`

**Steps:**
1) 区分两类泄露：系统 DNS（LAN/IPv6）绕过 tun、代理模式域名解析走系统 resolver。
2) 对齐 VT 端“无泄露”前提（NetworkExtension 接管 DNS/路由 vs 终端 tun 自己加路由）。

---

### Task 2: terminal profile 增加 proxy-mode 防泄露规则

**Files:**
- Modify: `scripts/build_config.py`
- Test: `tests/test_pipeline.sh`

**Steps:**
1) 对 terminal profile 注入 `{"inbound":"mixed-in","action":"resolve"}`（让代理模式的域名解析走 sing-box DNS 路由）。
2) 将 terminal 的 tun 入站默认 `sniff_override_destination=false`（减少由“目的地覆盖为域名”触发的额外解析链路）。
3) 更新测试断言覆盖上述行为。

---

### Task 3: macOS DNS guard 加固（IPv6 + 服务选择 + flush）

**Files:**
- Modify: `fly`

**Steps:**
1) DNS guard 选择“当前有 IP 的网络服务”，避免 VPN 启动后默认接口/路由变化导致映射失败。
2) 同时设置 IPv4/IPv6 公网 DNS（避免 IPv6 resolver 仍走本地链路导致泄露）。
3) 应用/恢复后 flush DNS cache（`dscacheutil -flushcache` + `killall -HUP mDNSResponder`）。

---

### Task 4: 验证与回归

**Files:**
- Test: `tests/test_pipeline.sh`

**Commands:**
- `bash -n fly`
- `conda run -n yellow python -m py_compile scripts/build_config.py scripts/build_route_rules.py scripts/extract_nodes.py`
- `bash tests/test_pipeline.sh`

**Manual checks (macOS):**
- `./fly build-config --profile terminal --ruleset`
- `./fly on --config config.terminal.json`
- 使用 DNS leak test 站点确认无 “ISP/LAN resolver” 泄露，并观察 `networksetup -getdnsservers "<service>"` 在 `on/off` 前后是否按预期变更/恢复。

