# Bulianglin 配置逻辑借鉴笔记（DNS 防泄露方向）

> 说明：本笔记主要基于你提供的 `example/config.json` 与 `example/tun.json` 做逻辑分析。  
> 原教程页面 `https://bulianglin.com/archives/singbox.html` 当前有 Cloudflare 验证，自动抓取失败，所以这里不直接引用正文。

## 1. 先说结论（你现在有没有做到）

你当前自动生成的 VT `1.11.4` 兼容配置，已经具备了 DNS 防泄露里最关键的几项：

- 有 `tun` 入站（桌面端还带 `mixed`）并开启 `auto_route` / `strict_route`
- 有前置 `hijack-dns` 路由规则（把系统 DNS 流量接管到 sing-box 内部 DNS）
- 有单独的 DNS 直连出口（`dns_direct`），避免 DNS 解析和代理节点解析互相套娃
- DNS 里有分流规则（节点域名 bootstrap -> `local`，Google/YouTube/GitHub -> `google`）
- 有 QUIC `reject`（减少部分场景下因为 UDP/443 导致的异常）

从“是否会出现明显 DNS 泄露/乱走系统 DNS”这个角度看，**已经不是裸奔配置**。

## 2. 大佬配置在 DNS 防泄露上做了什么（核心逻辑）

从 `example/config.json` 看，他的思路非常清晰：**把 DNS 当成单独的数据平面来设计**。

### 2.1 DNS 服务器分角色

- `default-dns`：本地/国内 DNS（`223.5.5.5`），走 `direct-out`
- `system-dns`：系统 DNS（`address: local`），也走 `direct-out`
- `block-dns`：返回 `rcode://name_error`（用于拦截特定查询类型）
- `google`：远程 DoH（`https://dns.google/dns-query`）

这意味着他不是“一个 DNS 打天下”，而是按场景选择不同 resolver。

### 2.2 DNS 规则优先于路由规则来控解析路径

他在 `dns.rules` 里做了几件重要的事：

- `clash_mode=direct` 时，DNS 走本地 resolver
- `clash_mode=global` 时，DNS 走 Google DoH
- `rule_set=cnsite` 时，DNS 走本地 resolver
- `query_type=HTTPS` 时，直接丢到 `block-dns`

这套设计的价值是：**先控制“怎么解析”，再控制“解析后怎么走”**。

### 2.3 路由层强制接管 DNS

`route.rules` 里有两条关键规则：

- `inbound=dns-in -> dns-out`
- `protocol=dns -> dns-out`

本质是把 DNS 请求明确导向 sing-box 的 DNS 处理链，减少旁路。

## 3. 你这边和他相比，哪些已经对齐

你当前生成配置（VT 1.11.4 版本）已经对齐了他的一些关键思想，只是实现方式更偏客户端场景：

- 已有 DNS 接管：你用的是 `action: hijack-dns`（而不是 `dns-in/dns-out` 特殊出口）
- 已有 DNS 专用直连出口：你是 `dns_direct`，他是 `direct-out`
- 已有本地/远程 DNS 分工：`local` + `google`
- 已有模式切换 DNS 规则：`clash_mode=direct/global`
- 已有 TUN 严格路由：`strict_route=true`

也就是说，你现在的方向是对的，只是还可以把“DNS 分流策略”做得更精细。

## 4. 可以借鉴的点（按优先级）

### A. 高优先级（建议先评估）

### A1. 增加“CN 域名 -> 本地 DNS，非 CN -> 远程 DNS”的可选策略

你当前配置里 `dns.final=local`，这会让大量未命中的域名解析走本地 DNS。  
如果你更重视 DNS 隐私（而不是兼容性优先），可以借鉴他的思路：

- `dns.final` 改为远程 DNS（如 `google`）
- 再增加 `dns.rules`：`rule_set=geosite-cn`（或你的 `qx-china`）走 `local`

这样会更像：

- 国内域名：本地解析（速度/可用性好）
- 国外域名：远程解析（隐私更好、避免运营商污染）

注意：这项要做成“可选模式”，因为有些网络环境对 Google DNS/DoH 不友好。

### A2. 增加 DNS 策略模式开关（兼容优先 / 隐私优先）

你现在项目是面向 VT `1.11.4`，兼容性优先没有问题。  
建议后续做一个配置级开关（不是命令行也行）：

- `compat`（当前默认）
- `privacy`（借鉴大佬思路）

这样不会把“能用”和“更强防泄露”绑死在一起。

### B. 中优先级（可选增强）

### B1. 增加 `system-dns` 作为兜底 resolver（可选）

大佬配置里有 `address: local` 的 `system-dns`，这个对一些特殊网络（公司网、校园网、运营商劫持环境）可能有帮助。  
你可以考虑作为兜底项，而不是默认启用。

### B2. 增加 `query_type=HTTPS -> block` 的可选项

这条规则不是“防 DNS 泄露”的核心，但在某些环境下能减少 HTTPS/SVCB 记录引发的奇怪行为。  
建议做成可选开关，不要默认强开（避免兼容性副作用）。

### B3. 如果改用域名 DoH，记得补 bootstrap resolver

大佬的 `google` 用了：

- `address_resolver`
- `address_strategy`

这是为了防止 DoH 域名自身解析时走错路径。  
你目前用的是 `tls://8.8.8.8`（IP 直连），天然绕过了这个问题；如果未来切成 `https://dns.google/dns-query`，就要把这套补上。

### C. 低优先级（不建议直接照搬）

### C1. `dns-in` / `dns-out` / `block-out` / `direct-out` 整套旧写法

这个在他的场景（看起来更像路由器/OpenWrt/HomeProxy）是合理的。  
但你现在目标是 VT `1.11.4` 客户端 + 你的生成器逻辑，直接照搬会把结构复杂度拉高，而且未来升级内核时还会碰到 legacy special outbounds 的迁移问题。

你现在用 `hijack-dns` + 内置 DNS + `dns_direct` 的方案，更适合你这个项目。

### C2. `tun.json` 的参数原样照搬

`example/tun.json` 更像某个场景下的单独 tun 入站片段（例如 OpenWrt/旁路网关）：

- `inet4_address`
- `mtu: 9000`
- `gso: true`
- `sniff_override_destination: false`

这些不是“防 DNS 泄露”的核心参数。  
尤其 `mtu/gso` 和客户端平台兼容性相关，不能直接套到 VT 客户端。

## 5. 我建议你后续怎么借鉴（不改代码版草案）

可以按下面顺序推进（每一步都先做成可选）：

1. 先保持当前默认（兼容优先，已能稳定运行）
2. 新增“DNS 隐私模式”设计草案：
   - `dns.final=google`
   - `dns.rules` 增加 `cn rule_set -> local`
   - 保留 `dns_direct`
3. 再评估是否需要：
   - `system-dns` 兜底
   - `query_type=HTTPS` 拦截
4. 最后再考虑性能/平台项：
   - `sniff_override_destination` 开关
   - `mtu/gso` 等平台特化参数（仅特定平台模板）

## 6. 验证“是否真的防泄露”的建议（后续做实验时用）

后续如果你准备做这块优化，建议每次都做同一套验证：

- 导入后检查 sing-box 日志里 DNS 请求是否都走你预期的 resolver（`local` / `google`）
- 在不同模式（规则 / 全局 / 直连）下分别测试 DNS 行为
- 检查是否出现节点域名解析递归（DNS loop）或启动卡死
- 做一次 DNS 泄露测试（只看是否出现意料之外的 resolver/地区）

---

如果你认可这份思路，下一步我可以基于它再给你写一个“最小改造方案”（只改配置生成，不动规则转换逻辑）。
