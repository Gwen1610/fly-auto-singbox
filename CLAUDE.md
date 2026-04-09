# CLAUDE.md

本文件为 Claude Code 提供对此仓库的全局指导。

---

## 项目纲领

`fly-auto-singbox` 的目标是：**在终端用一套命令，安全、私密地管理 sing-box 的完整生命周期**。

核心原则（优先级从高到低）：

1. **隐私与防泄露优先**：DNS 请求不能绕过 sing-box；系统 DNS 不能被旁路；不在代码/配置中暴露订阅 URL 或节点信息。
2. **双端稳定可用**：桌面（VT 1.11.4 / terminal 1.12+）与 iOS（VT 1.11.4）必须同时通过测试。
3. **流程自动化**：`./fly` 一条命令完成订阅提取→规则转换→配置生成→运行管理全流程。
4. **最小权限/最小暴露**：不引入不必要的出站、不使用已废弃的特殊出站（`block`/`dns`）、不使用 geosite/geoip 字段。

---

## 常用命令

```bash
# 安装依赖
python3 -m pip install -r requirements.txt

# 初始化（从 config_template/ 生成 config/ 下的用户配置文件）
./fly init

# ── 主流水线（顺序执行）──────────────────────────────────────
./fly extract                          # 从订阅提取节点 -> build/nodes.json
./fly build-rules                      # QX/Clash 规则转换 -> config/route-rules.json
./fly build-config                     # 生成桌面配置（VT 兼容）-> runtime-configs/config.json
./fly build-config --target ios        # iOS 配置 -> runtime-configs/config.ios.json
./fly build-config --target desktop --profile terminal  # 1.12+ 终端配置 -> runtime-configs/config.terminal.json

# ── Ruleset 模式（生成远端引用的小体积配置）────────────────────
./fly build-rules --ruleset --base-url "https://raw.githubusercontent.com/<user>/<repo>/main/ruleset"
./fly publish-ruleset                  # 提交 ruleset/*.srs 到 Git
./fly build-config --ruleset
./fly build-config --target ios --ruleset
./fly build-config --target desktop --profile terminal --ruleset

# ── 交互模式（数字键选择）──────────────────────────────────────
./fly build-rules --interactive
./fly build-config --interactive
./fly pipeline --interactive
./fly interactive                         # 统一交互入口

# ── 一步流水线 ──────────────────────────────────────────────
./fly pipeline
./fly pipeline --target ios --ruleset

# ── 运行管理 ────────────────────────────────────────────────
./fly on / ./fly off / ./fly status / ./fly log
./fly on --config config.terminal.json    # 显式指定启动配置（从 runtime-configs/ 解析）

# ── sing-box 安装 ───────────────────────────────────────────
./fly check-singbox
./fly install-singbox --version 1.11.4

# ── 测试（唯一入口）────────────────────────────────────────
bash tests/test_pipeline.sh
```

---

## 代码架构

### 主入口

`fly`（Bash 脚本）负责：环境变量加载（`config/fly.env`）、命令路由、sing-box 启停、macOS DNS guard、ruleset 发布（git add/commit/push）。所有 Python 逻辑通过 `python3 scripts/*.py` 调用。

### 三段式核心流水线

```
订阅 URL
   └─> scripts/extract_nodes.py         -> build/nodes.json
          (过滤 US/HK/SG/JP；支持 SS/VMess/VLESS/Trojan/Hysteria2/TUIC/AnyTLS/WireGuard 等)
                  │
        config/rule-sources.json
   └─> scripts/build_route_rules.py     -> config/route-rules.json
                                           config/route-rules.ruleset.json   (--ruleset)
                                           ruleset/*.json + *.srs             (--ruleset)
                  │
        config/base-template.json       (桌面)
        config/base-template.ios.json   (iOS)
        config/group-strategy.json
   └─> scripts/build_config.py          -> runtime-configs/config.json
                                           runtime-configs/config.terminal.json
                                           runtime-configs/config.ios.json
```

### build_config.py 注入逻辑

在模板基础上自动注入两类内容：

**1. Outbounds（分组拓扑）**

| 分组类型 | 示例 tag | 策略 |
|---|---|---|
| 来源+地区组 | `A-HongKong` | HK/SG/JP 用 `urltest`；America 用 `selector` |
| 地区聚合组 | `HongKong` | `region_defaults` 控制默认值 |
| 业务/自定义组 | `Streaming`、`AI` | 来自 `group-strategy.json` |
| 顶层 | `Proxy` | 聚合所有地区组 |

**2. 连通性默认规则（route + dns）**

- `hijack-dns` 接管 DNS 入口
- QUIC reject（`protocol=quic` + `udp:443`）
- `ip_is_private -> direct`
- DNS 服务器注入：`default-dns`、`system-dns`（可选兜底）、`block-dns`、`google`
- `dns.final = "google"`、`dns.strategy = "ipv4_only"`

---

## DNS 防泄露架构

> 这是本项目的核心安全原则，改动此区域必须通过完整测试。

### 当前防泄露层次

| 层 | 机制 | 作用 |
|---|---|---|
| TUN inbound | `strict_route: true` + `auto_route: true` | 强制全流量进入 sing-box |
| route 层 | `hijack-dns` rule（最高优先级） | 系统 DNS 查询被接管 |
| DNS 层 | `dns_direct` 专用直连出口 | 避免 DNS 解析走代理节点（套娃） |
| DNS 分流 | CN 域名 → `local`（Ali DoH），其余 → `google`（TLS DoH） | 国内快解析 + 国外隐私解析 |
| macOS 运行期 | `MACOS_DNS_GUARD=true` | `./fly on` 时临时将系统 DNS 指向 tun 地址，fail-closed |
| macOS watchdog | `MACOS_DNS_GUARD_WATCHDOG=true` | sing-box 异常退出时自动恢复系统 DNS |
| terminal profile | `mixed-in` 注入 `resolve` action | 代理模式域名解析走 sing-box DNS，不走系统 resolver |

### DNS 服务器角色定义（Bulianglin 风格）

```
default-dns   → 本地/国内（223.5.5.5 Ali DoH），走 direct
system-dns    → address: local，作为特殊网络（校园网/公司网）兜底
block-dns     → rcode://name_error，拦截 HTTPS/SVCB 查询类型
google        → tls://8.8.8.8 或 https://dns.google/dns-query，走 Proxy
```

> 若切换为 `https://dns.google/dns-query`（域名形式 DoH），必须补 `address_resolver`（bootstrap）以防 DoH 域名自身解析递归。目前用 `tls://8.8.8.8`（IP 直连）可绕过此问题。

### DNS 泄露验证步骤

每次修改 DNS/route 逻辑后必须执行：

1. `bash tests/test_pipeline.sh`（生成三端配置不报错）
2. `./fly on --config config.terminal.json`（终端模式启动）
3. 检查 sing-box 日志：DNS 请求是否都走预期 resolver
4. 在规则/全局/直连三种模式下各测一次 DNS 行为
5. 访问 `https://dnsleaktest.com/` 或 `https://ipleak.net/` 确认无意外 resolver 出现
6. `./fly off` 后确认 `networksetup -getdnsservers <service>` 恢复原值

---

## VT 1.11.4 兼容策略

### 目标版本矩阵

| 目标 | 命令 flag | 输出文件 | 内核要求 |
|---|---|---|---|
| 桌面 VT（默认） | `--profile vt`（默认） | `config.json` | VT ≥ 1.11.4 |
| iOS VT | `--target ios` | `config.ios.json` | VT iOS ≥ 1.11.4 |
| 终端 1.12+ | `--profile terminal` | `config.terminal.json` | sing-box ≥ 1.12 |

### iOS 兼容处理（`--target ios`）

- 清除 `dns.servers[].type` 字段（VT 1.11.4 不支持，会崩溃）
- 清除 `route.default_domain_resolver`（同上）
- 只保留 `tun` inbound（不含 `mixed`）
- 更保守的 DNS / route 注入

### terminal profile 与 vt profile 的区别

`terminal` 只改兼容字段，**不改变**分组拓扑、分流规则、连通性默认注入：

- 使用 1.12+ 新 DNS server 格式（含 `type` 字段）
- 按出站注入 `domain_resolver`（减少终端告警）
- 对 `mixed-in` 注入 `resolve` action（防代理模式 DNS 泄露）
- 保持 `clash_mode=direct -> default-dns`（避免退回 system-dns）

---

## 关键约束（不可违反）

- **双端必须同时可用**：修改 DNS / route 逻辑后，桌面与 iOS 两端都必须通过 `bash tests/test_pipeline.sh`。
- **不使用旧版特殊出站**：`block` / `dns` 不能出现在 `route.rules[].outbound`，应用 `action: reject` / `action: hijack-dns`。
- **`direct` / `block` 不出现在最终 outbounds 列表**：由 `dns_direct` 等内部出站代替。
- **不使用 geosite/geoip 字段**：所有 GeoIP/GeoSite 走 `rule_set`（sing-box 1.8+ 迁移方向）。
- **`example/` 目录禁止提交**：可能含敏感订阅信息，禁止 `git add` / `push`。

---

## 配置文件说明

| 文件 | 说明 |
|---|---|
| `config/fly.env` | 所有路径与运行参数的环境变量（优先在此调整） |
| `config/base-template.json` | 桌面 sing-box 配置骨架（inbounds/dns/route 基础结构） |
| `config/base-template.ios.json` | iOS sing-box 配置骨架（仅 tun inbound，无 mixed） |
| `config/group-strategy.json` | 分组结构（地区默认值、业务组、Proxy 成员） |
| `config/route-rules.json` | 分流规则（`build-rules` 生成或手工编辑） |
| `config_template/*.example*` | `./fly init` 的来源模板，不直接参与运行 |
| `runtime-configs/` | 生成的运行配置，不提交 Git |
| `build/nodes.json` | 提取的节点，不提交 Git |

### 关键环境变量（`config/fly.env`）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `CONFIG_OUTPUT_DIR` | `./runtime-configs` | 配置输出目录 |
| `MACOS_DNS_GUARD` | `true` | macOS 下启动时接管系统 DNS |
| `MACOS_DNS_GUARD_WATCHDOG` | `true` | sing-box 异常退出时自动恢复系统 DNS |

---

## 常见错误排查

| 错误信息 | 原因 | 排查方向 |
|---|---|---|
| `dns.servers[0].type unknown field` | iOS/VT 1.11.4 收到新格式 DNS 配置 | 检查 `build_config.py` iOS 分支是否正确清除了 `type` 字段 |
| `outbound detour not found: direct` | DNS 规则引用了不存在的 outbound | 检查 `dns.rules[].server` 引用的 outbound tag 是否存在 |
| ruleset 拉取 404 | `RULESET_BASE_URL` 配置错误或未 push | 检查 `fly.env` 里的 URL + 确认 `./fly publish-ruleset` 成功 |
| `no US/HK/SG/JP nodes found` | 节点名称不含地区关键词 | 检查订阅节点名称，参考 `build_config.py` 中的 `REGION_PATTERNS` |
| DNS 泄露到 ISP/LAN resolver | 系统 DNS 未被 guard 覆盖 | 检查 `MACOS_DNS_GUARD` 是否生效；检查 IPv6 resolver 是否被一并覆盖 |
| 代理模式走系统 DNS | terminal profile 未注入 resolve action | 检查 `mixed-in` 是否有 `action: resolve` 规则 |

---

## 未来工作（`docs/future-work.md`）

- DNS 隐私模式开关：`compat`（兼容优先，当前默认）vs `privacy`（`dns.final=google`，CN 域名 → `local`）
- QUIC 屏蔽做成可选项（按域名放开）
- `urltest` 参数（interval / tolerance / probe URL）下沉到用户配置
- IPv6 策略：双栈 / prefer IPv6 / IPv4-only 可选
- 诊断模式：更保守的路由 + 更详细日志

---

## 外部参考资源

### sing-box 官方

| 资源 | 链接 |
|---|---|
| 官方 GitHub | `https://github.com/SagerNet/sing-box` |
| 官方文档 | `https://sing-box.sagernet.org/` |
| Migration 指南 | `https://sing-box.sagernet.org/migration/` |
| DNS 配置文档 | `https://sing-box.sagernet.org/configuration/dns/` |
| Releases 页面 | `https://github.com/SagerNet/sing-box/releases` |

### 不良林（bulianglin）—— DNS 防泄露参考

| 资源 | 链接 |
|---|---|
| sing-box 配置教程 | `https://bulianglin.com/archives/sing-box.html` |
| GitHub 主页 | `https://github.com/bulianglin` |
| homeproxy（ImmortalWrt 代理平台，基于 sing-box）| `https://github.com/bulianglin/homeproxy` |
| psub（CF Worker 订阅转换）| `https://github.com/bulianglin/psub` |

> 本项目 `docs/bulianglin-dns-leak-borrowing-notes.md` 是对其 DNS 防泄露设计的深度分析笔记，务必先读此文件。

### 规则集与分流

| 资源 | 链接 |
|---|---|
| blackmatrix7 iOS 分流规则（最全）| `https://github.com/blackmatrix7/ios_rule_script` |
| ACL4SSR Clash 规则集 | `https://github.com/ACL4SSR/ACL4SSR` |
| MetaCubeX（Clash Meta 维护者）| `https://github.com/MetaCubeX` |

### 代理协议参考

| 协议 | 文档链接 |
|---|---|
| VLESS | `https://xtls.github.io/en/config/outbounds/vless.html` |
| VMess | `https://www.v2fly.org/en_US/developer/protocols/vmess.html` |
| Trojan | `https://trojan-gfw.github.io/trojan/protocol.html` |
| Hysteria2 | `https://v2.hysteria.network/` |
| TUIC | `https://github.com/tuic-protocol/tuic/blob/master/SPEC.md` |
| XTLS REALITY | `https://github.com/XTLS/REALITY` |
| Xray-core | `https://xtls.github.io/` |
| V2Fly（v2ray-core 社区分支）| `https://github.com/v2fly/v2ray-core` |

### DNS 泄露测试工具

| 工具 | 链接 |
|---|---|
| dnsleaktest.com（最常用）| `https://dnsleaktest.com/` |
| ipleak.net（IP + DNS 综合）| `https://ipleak.net/` |
| browserleaks DNS | `https://browserleaks.com/dns` |
| dnscheck.tools | `https://dnscheck.tools/` |
| browserscan DNS leak | `https://www.browserscan.net/dns-leak` |

### 本项目内部文档

| 文档 | 说明 |
|---|---|
| `docs/bulianglin-dns-leak-borrowing-notes.md` | DNS 防泄露设计深度分析（必读）|
| `docs/future-work.md` | 后续优化计划 |
| `docs/plans/` | 历史设计方案存档 |

> 查阅优先级：官方文档 > 本仓库分析文档 > 社区文章。版本基线为 VT `1.11.4`，1.12+ 新格式修改建议做版本开关而非直接替换。
