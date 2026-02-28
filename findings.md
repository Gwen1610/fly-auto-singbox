# Findings

## 2026-02-12
- 用户要求对 `fly-auto-singbox` 进行解耦重构，并直接提交推送到远端仓库。
- 新架构分为三块：
  1) sing-box 手动下载/安装指导（不自动化）；
  2) 节点提取与分流构建拆分成两个独立模块；
  3) 运行态进程管理 `on/off/status/log`。
- `sing-box-subscribe` 作为外部已维护项目，不在本仓库直接修改。
- 已完成实现：
  - 新 `fly` 命令面：`init/install-guide/extract/build-config/pipeline/on/off/status/log`。
  - 新模块：`scripts/extract_nodes.py`（Only-nodes 提取）和 `scripts/build_config.py`（分流注入）。
  - 新配置：`config/fly.env.example`、`config/extract.providers.example.json`、`config/base-template.json`、`config/route-rules.json`。
  - 新测试：`tests/test_pipeline.sh`。
- 验证结果：
  - `bash tests/test_pipeline.sh` 通过。
  - `bash -n fly` 通过。
  - `python3 -m py_compile scripts/extract_nodes.py scripts/build_config.py` 通过。
- Git 交付：
  - commit: `5210806` (`refactor: decouple fly pipeline into extract/build/runtime modules`)
  - push: 已推送到 `origin/main`（远端提示仓库新地址为 `https://github.com/Gwen1610/fly-auto-singbox.git`）

## 2026-02-12 (auto install extension)
- 新增 `install-singbox` 自动安装命令，支持：
  - OS: `linux` / `darwin`
  - ARCH: `amd64` / `arm64`
  - 参数：`--version` `--install-dir` `--dry-run` `--releases-json`
- `install-guide` 改为兼容别名，等价 `install-singbox --dry-run`。
- 解析资产方式为 GitHub Releases 元数据解析，不硬编码文件名。
- 测试仅使用 `--dry-run` + 本地 mock `releases.json`，未触发真实下载。
- 验证结果：
  - `bash -n fly` 通过
  - `bash tests/test_pipeline.sh` 通过
  - `python3 -m py_compile scripts/extract_nodes.py scripts/build_config.py` 通过

## 2026-02-12 (internal extractor extension)
- 已将订阅提取所需代码内置到仓库：`scripts/internal_subscribe/`。
- `scripts/extract_nodes.py` 已改为本地实现，不再 subprocess 调用外部 `sing-box-subscribe/main.py`。
- 默认流程现在仅依赖本仓库代码 + Python 依赖（`requests`、`PyYAML`）。
- 提取器新增无 `requests` 兼容路径：无该依赖时自动回退到 `urllib`。
- README 已补充必要信息：
  - 安装后校验命令（`which sing-box` / `sing-box version`）
  - 订阅填写位置（`config/extract.providers.json`）
  - 节点输出位置（`build/nodes.json`）
  - 最终配置输出位置（`config.json`）

## 2026-02-12 (install flow polish)
- 新增 `./fly check-singbox`：用于安装前检查本机是否已安装及当前版本。
- `install-singbox` 新增：
  - 已安装同版本时自动跳过下载；
  - `--force` 可强制重装；
  - `--dry-run` 会显示 `will_skip` 决策结果。
- README 增加开源来源署名：
  - 提取器来源项目：`Toperlock/sing-box-subscribe`
  - 原作者：`Toperlock`

## 2026-02-12 (extract compatibility fix)
- 发现线上报错 `no US/HK/SG/JP nodes found after filtering` 的主要原因是地区正则过严，无法覆盖 `US01/HK01/SGP/JP` 等常见命名。
- 已放宽 `extract` 和 `build-config` 的地区识别规则，并同步到 `internal_subscribe/tool.py`。
- `extract` 报错现在会返回 sample tags，方便定位节点命名是否可识别。
- 已新增 `config_template/minimal_four_regions.json` 兼容文件，避免旧路径引用报缺失。
- 进一步修复：从 `SHARE_PREFIXES` 移除 `http://` 和 `https://`，避免把订阅 URL 误判为节点 URI，导致不下载订阅内容。
- `extract.providers` 示例默认 `enabled` 调整为 `true`，降低初始化后踩坑概率。

## 2026-02-12 (route rules template + default no-split)
- 已将默认分流文件从仓库内固定 `config/route-rules.json` 调整为参考模板 `config/route-rules.example.json`。
- `./fly init` 现在会自动从 `route-rules.example.json` 生成可编辑的 `config/route-rules.json`。
- 默认路由策略改为不含分流规则：
  - `final = Proxy`
  - `rules = []`
- `tests/test_pipeline.sh` 已同步改为校验 `config.json` 中 `route.final=Proxy` 且 `route.rules` 为空。
- README 新增“配置文件作用”章节，明确：
  - `config/base-template.json`：运行时主模板；
  - `config_template/minimal_four_regions.json`：旧路径兼容模板；
  - `config/route-rules.example.json`：分流规则参考模板。

## 2026-02-12 (remove legacy geosite/geoip strategy)
- 用户要求彻底移除历史预置分流策略（包括 `geosite-category-ads-all`、`geoip-cn` 等）。
- 已从 `config/base-template.json` 删除所有 `route.rule_set` 与 DNS 中 `rule_set` 相关内容。
- 现在默认模板只保留基础网络结构，不内置任何基于 geosite/geoip 的策略。
- `config_template/minimal_four_regions.json` 已删除，模板来源统一为 `config/base-template.json`。
- 测试新增断言：生成的 `config.json` 不应包含 `geosite` 或 `geoip` 字样。

## 2026-02-12 (terminal colors + markdown cleanup)
- `fly` 增加终端彩色输出：
  - 蓝色：普通 `[fly]` 日志；
  - 黄色：`warn`、`not running`、`already running`；
  - 红色：`die` 错误；
  - 绿色：`started/stopped/running`。
- 彩色输出仅在交互终端启用；当输出被重定向/管道时自动降级为纯文本，不影响脚本与测试解析。
- 支持通过 `NO_COLOR=1` 手动关闭颜色。
- markdown 收尾：为 `docs/plans/*` 增加 archive note，提示以 `README.md` 为当前行为准。

## 2026-02-12 (integrate sing-box-geosite style rule conversion)
- 新增独立命令 `./fly build-rules`，专门把 QX/Clash 规则源转换为 `config/route-rules.json`。
- 新增配置模板 `config/rule-sources.example.json`，`./fly init` 会自动生成可编辑的 `config/rule-sources.json`。
- 新增脚本 `scripts/build_route_rules.py`：
  - 支持 `.list/.yaml/.txt`；
  - 支持常见规则映射：`DOMAIN-SUFFIX/DOMAIN/DOMAIN-KEYWORD/IP-CIDR/...` 到 sing-box 对应字段；
  - 输出格式为 `{final, rules}`，直接被 `build-config` 消费。
- 转换模块保持解耦：仅生成 `route-rules.json`，不触碰节点提取或运行态命令。
- 兼容性修复：
  - 无 `requests` 时自动回退到 `urllib`；
  - 无 `PyYAML` 时使用最小 `payload` 解析回退；
  - 相对路径规则源支持 `sources 文件目录` 与 `当前工作目录` 双路径解析。


## 2026-02-12 (manual supplements + outbound alias normalization)
- 新增 `manual_rules` 字段：可直接在 `config/rule-sources*.json` 写 QX 单行规则（例如 `DOMAIN-SUFFIX, ai.dev, America`）。
- `build_route_rules.py` 现在会解析 `manual_rules` 并合并到输出 `route-rules.json`。
- 出口别名自动规范化：
  - `Direct -> direct`
  - `Reject -> block`
- `build_config.py` 已增加 `block` outbound，并在校验阶段对 `final/outbound` 做同样的别名规范化。
- 你的补充规则模式（`DOMAIN-SUFFIX/HOST/HOST-KEYWORD/GEOIP`）均已覆盖并通过测试。

## 2026-02-12 (template directory normalization)
- 按用户建议将所有 `.example` 模板统一迁移到 `config_template/`：
  - `fly.env.example`
  - `extract.providers.example.json`
  - `rule-sources.example.json`
  - `route-rules.example.json`
- `fly init` 已改为从 `config_template/` 复制生成运行时文件到 `config/`。
- README 已同步改为 `config_template/*.example` 路径说明。

## 2026-02-12 (hierarchical grouping strategy)
- 分组模型已升级为四层：
  1) 来源+地区（`A-HongKong`/`B-HongKong`）；
  2) 地区聚合（`HongKong` 包含来源子组）；
  3) 业务组（`Streaming`/`AI` 等）；
  4) 顶层 `Proxy`。
- `extract_nodes.py` 现在会在节点中保留 `__provider_tag`，作为来源分组依据。
- `build_config.py` 新增 `--groups-file`，读取 `config/group-strategy.json` 来决定：
  - 各地区默认来源（如 `HongKong -> A`）；
  - 业务组成员与默认值；
  - 顶层 `Proxy` 成员与默认值。
- 新增模板：`config_template/group-strategy.example.json`。
- `fly init` 与 `fly.env` 已接入 `GROUP_STRATEGY_FILE`，`build-config` 执行时强制校验该文件存在。

## 2026-02-12 (connectivity defaults + urltest regions)
- 现象：Safari 访问 Google/YouTube 时倾向优先走 QUIC（UDP 443），在部分代理链路上会导致卡死或回落慢。
- 现象：当 DNS server 设置为 `detour=Proxy` 且节点 `server` 需要 DNS 解析时，会触发 `DNS query loopback in transport[...]`（DNS 解析递归闭环）。
- 解决：`build-config` 现在会注入连通性默认行为，避免用户手改 `config.json`：
- 解决：入站启用 `sniff` + `sniff_override_destination`。
- 解决：路由前置注入 `hijack-dns`、QUIC `reject`（`protocol=quic` / `udp:443`）、以及 `ip_is_private -> direct`。
- 解决：DNS 注入 `local` 与 `google` server，并通过规则让“节点域名 bootstrap 走 local”，同时让 Google/YouTube 域名走 `google`。
- 分组体验：`HongKong/Singapore/Japan` 的来源+地区子组默认使用 `urltest` 自动选最快；`America` 保持 `selector` 手动选择。
- 补充：新增 `docs/future-work.md` 记录后续可选优化（开关化 QUIC、PSL、IPv6 策略、urltest 参数等）。

## 2026-02-27 (sing-box Clash API + TUI 方案调研)

### sing-box Clash API 核心能力

sing-box 通过 `experimental.clash_api` 提供 Clash 兼容的 RESTful HTTP API，核心能力如下：

**启用配置：**
```json
{
  "experimental": {
    "clash_api": {
      "external_controller": "127.0.0.1:9090",
      "secret": "your-secret"
    }
  }
}
```

**关键 API 端点：**

| 操作 | 端点 | 方法 |
|---|---|---|
| 列出所有出站 | `GET /proxies` | GET |
| 动态切换 selector 出站 | `PUT /proxies/{name}` body: `{"name":"target-tag"}` | PUT |
| 单出站延迟测试 | `GET /proxies/{name}/delay?url=...&timeout=5000` | GET |
| 组内全部出站测速 | `GET /group/{name}/delay?url=...&timeout=5000` | GET |
| 实时流量统计（支持 WS） | `GET /traffic` | GET/WS |
| 实时日志流（支持 WS） | `GET /logs` | GET/WS |
| 连接管理 | `GET/DELETE /connections` | GET/DELETE |
| 模式切换 | `PATCH /configs` body: `{"mode":"Rule"}` | PATCH |

**动态切换出站（不重启）：**
```bash
curl -s -X PUT "http://127.0.0.1:9090/proxies/HongKong" \
  -H "Authorization: Bearer secret" \
  -H "Content-Type: application/json" \
  -d '{"name": "A-HongKong"}'
# 返回 204 No Content = 成功
```

**延迟测试注意：** `http://` URL 有 bug，建议使用 `https://www.gstatic.com/generate_204`；`timeout` 单位毫秒，最大 32767ms。

**`GET /proxies` 中 selector 类型示例：**
```json
{
  "HongKong": {
    "type": "Selector",
    "now": "A-HongKong",
    "all": ["A-HongKong", "B-HongKong"],
    "history": [{"time": "...", "delay": 45}]
  }
}
```

### TUI 方案技术调研结论

**Tide `configure` 核心机制：**
- 纯 Fish Shell，零依赖
- `read --nchars 1` 捕获单字符（数字键，不是箭头键）
- 选项格式：`(1) Option A`，按数字选择

**Bash 移植（最小依赖）：**
- `IFS= read -rsn1 key` 捕获单字符
- `tput smcup/rmcup` 备用屏幕缓冲区
- `printf '\033[H'` 回顶刷新（不 clear，避免闪烁）
- `IFS= read -rsn1 -t N key` 定时自动刷新

**方案选型：**
| 场景 | 选择 | 理由 |
|---|---|---|
| 节点切换向导 | 纯 Bash `read -rsn1` + ANSI | 零依赖，fly 已有 ANSI 基础设施 |
| 实时监控面板 | Bash `read -t` + curl 调 Clash API | 无额外依赖 |
| （可选增强）节点模糊搜索 | `fzf` 可选 | 单文件二进制 |

---

## 2026-02-23 (bulianglin DNS anti-leak logic review, no code changes)
- 原教程页面 `https://bulianglin.com/archives/singbox.html` 自动抓取时被 Cloudflare 验证拦截，无法直接读取正文；本轮分析基于用户提供的 `example/config.json` 和 `example/tun.json`。
- 对方配置的核心思路是“DNS 单独建模”：多 resolver 分角色（本地 / system / block / 远程 DoH），再用 `dns.rules` 决定解析路径。
- 当前项目（VT 1.11.4 兼容版）已经具备关键防泄露基础：`strict_route`、`hijack-dns`、DNS 专用直连出口 `dns_direct`、本地/远程 DNS 分工与模式规则。
- 可借鉴的主要增强方向：把 `dns.final=remote` + `CN rule_set -> local` 做成“隐私优先”可选模式；`system-dns` 与 `query_type=HTTPS` 拦截可作为后续可选项。

## 2026-02-27（交互式构建 + 终端兼容档位）
- 本机终端 sing-box 版本为 `1.12.21`（`sing-box version` 实测）。
- 官方 Migration（1.12）明确提示三类迁移：
  - `legacy DNS servers` -> 新 `dns.servers` 格式（`type/server/...`）
  - `outbound DNS rule item` -> `domain_resolver`
  - 缺少 `route.default_domain_resolver` 或 dial fields `domain_resolver` 会告警
- 结论：需保留双档配置：
  - `vt` 档（兼容 VT 1.11.4，legacy DNS）
  - `terminal` 档（1.12+，新 DNS server + resolver 迁移，避免终端告警）
- 交互路径设计定稿：
  1) 第一层：`iOS` / `电脑端`
  2) 第二层：`有 Rule Set` / `无 Rule Set`
  3) 第三层（仅电脑端）：`VT 1.11.4` / `终端 1.12+`

## 2026-02-27（fly on 交互启动 + terminal fatal 修复）
- 用户反馈终端启动 fatal：`start dns/udp[default-dns]: detour to an empty direct outbound makes no sense`。
- 根因：terminal profile 的 `default-dns`（新 DNS server 格式）仍携带 direct 类型 detour（`dns_direct`），在 1.12+ 下被判定为无意义并直接 fatal。
- 修复策略：
  - terminal profile 的 `default-dns/system-dns/google` 去掉 direct-type detour；
  - 保留 `domain_resolver` + 其它分流/连通性逻辑；
  - 继续避免 deprecated 的 `dns.rules[].outbound=any`。
- 为避免 terminal 档出现与 VT 不一致的 DNS 行为，`clash_mode=direct` 已改回 `default-dns`（不走 `system-dns`）。
- 新增统一交互入口 `./fly interactive`（别名 `./fly menu`），可在同一界面选择提取节点/生成规则/构建配置。
- 结论：功能未删减，核心能力（分层分组、route 规则注入、hijack-dns/QUIC reject、CN 规则联动）保持不变，仅替换兼容字段表达方式。

## 2026-02-27（terminal DNS 泄露复盘 + 配置目录统一）
- 复盘官方迁移文档后确认：**legacy DNS server（无 detour）默认走“默认出站”**，而 **new DNS server（无 detour）默认走“空 direct 出站”**。
- 这会导致 VT 逻辑迁移到 terminal profile 时出现行为偏移：同样“未写 detour”的 `google` DoH server 在 terminal 下会直连，而不是沿用默认代理路径。
- 结论：terminal profile 需对 `google` server 显式设置 `detour=Proxy`，才能与 VT 防泄露意图一致，同时继续避免 1.12+ 的 deprecated 告警。
- 进一步排查发现：terminal profile 里的全局 `route.default_domain_resolver=default-dns` 也会扩大 direct 解析影响面，和 VT 语义存在偏移。
- 修正方案：移除全局 `route.default_domain_resolver`，改为给 terminal 档的 dial outbounds 注入 `domain_resolver=default-dns`（含 `dns_direct` 和节点出站），保持 VT 行为同时满足 1.12+ 迁移要求。
- 仍可能出现的“终端 DNS 泄露”常见根因（macOS）：系统 DNS 来自路由器/LAN 私网地址（DHCP 下常见），而 tun 的 auto_route 默认不会覆盖更具体的 LAN 路由，导致 DNS 查询直接走物理网卡绕过 tun（VT 客户端会通过系统 VPN 机制接管 DNS，因此不复现）。
- 工程化修复：在 `fly on/off` 增加 macOS DNS guard（启动 tun 配置时临时把系统 DNS 指向 tun 网段内地址，以 fail-closed 的方式减少这类泄露的环境依赖，并在停止时恢复）。
- DNS guard 补强：优先选择“当前有 IP 的网络服务”（避免 VPN 启动后默认路由接口变为 `utun*` 导致映射失败）；同时设置 IPv4/IPv6（若系统不接受 IPv6 DNS 自动回退 IPv4-only）；并在应用/恢复后 flush 系统 DNS cache；并可选启动 root watchdog，sing-box 异常退出时也能自动恢复系统 DNS（避免残留）。
- terminal profile 补强：对 `mixed-in` 注入 `route.rules[].action=resolve`（代理模式下由 sing-box DNS 统一解析，避免走系统 DNS）；并将 tun 入站的 `sniff_override_destination` 默认关闭（减少由“覆盖目的地为域名”触发的额外解析链路）。
- 同步完成配置产物目录统一：
  - 默认 `CONFIG_OUTPUT_DIR=./runtime-configs`
  - `CONFIG_JSON/CONFIG_JSON_IOS/CONFIG_JSON_TERMINAL` 默认全部落在该目录
  - `fly on` 交互扫描目录切换到 `runtime-configs/`，支持自命名 `*.json`。

## 2026-02-28 (direct 分流不生效排障)
- 用户反馈：分流规则中的 `direct` 全部未生效，已尝试多种方式仍失败。
- 排障策略：先本地证据采集（配置生成链路 + 运行日志），再对照官方文档和 GitHub 相似配置。
- 当前待验证假设：
  1) 规则语义层面：某些规则字段组合导致 AND 语义误匹配或零命中；
  2) 优先级层面：`direct` 规则位于后序，被更前置规则抢先命中；
  3) 出站/解析层面：规则命中后因为 DNS/出站配置联动，表现为“看起来仍走代理”。

### 2026-02-28 追加结论（root cause confirmed）
- 本地证据：`runtime-configs/config*.json` 中用户 `Direct` 规则在 `build_config.py` 阶段被改写为 `action: direct`，而运行日志显示 `www.bilibili.com` / `www.zhihu.com` / `gateway.icloud.com.cn` 等仍走代理节点。
- 官方文档对照：sing-box 1.11+ 迁移里仅 `block` / `dns` 作为“special outbound”迁移为 action；`direct` 仍应通过 outbound 路由（见 migration 文档 `Route Rule` 段落）。
- 官方 rule_action 文档显示 `action` 的终结动作是 `route`（带 `outbound` 参数），不存在独立 `action=direct` 语义。
- GitHub 参考配置（官方仓库 issue 样例）也普遍使用：`{"rule_set": [...], "outbound": "direct"}`。
- 结论：当前项目把 `direct` 转成 `action: direct` 是核心偏差，导致 direct 分流与官方语义不一致，表现为规则看似存在但不走直连。

## 2026-02-28（体验优先 + 启动可靠性 + log 连接层级）
- 体验优先：新增 `connectivity_mode`，默认 `experience`（保留 `hijack-dns` + 私网直连，不强制注入 QUIC reject）；`stable` 模式可恢复 QUIC reject。
- 启动可靠性：新增 `ruleset_reference_mode`，`auto` 下桌面端优先把 `route.rule_set` 的 `qx-*` 远程项改写为本地 `ruleset/<tag>.srs`，减少启动时远程下载失败/超时风险；iOS 仍保持远程 URL。
- 可观测性：`fly log` 新增 `--level conn`（别名 `outbound`），只输出 `outbound connection to ...` 行，便于实时看“节点连了哪个域名/IP”。
- 兼容边界：
  - `ruleset_reference_mode=local` 会在缺少本地 `.srs` 时直接构建失败（fail-fast）。
  - `prefer-local` 会在本地缺失时回退远程 URL（不中断构建）。

## 2026-02-28（网页速度优化研究与落地）
- 官方文档确认：`urltest` 支持 `interval`、`tolerance`（用于控制“延迟改善多少才切换”），可用于加快故障/抖动时的节点切换响应。
- 官方文档确认：DNS 有 `independent_cache`（按 server 独立缓存）；多 resolver 并存场景下可减少缓存串用导致的“命中异常 CDN / 解析行为漂移”。
- 社区配置（rewired）普遍做法：通过 `geosite-cn`/国内规则把国内域名解析和路由固定到本地链路，减少首开慢与绕路。
- 本轮落地：
  - 默认 urltest 从 `10m` 调整到 `5m`，默认 `tolerance=50ms`；
  - DNS 增加 `.cn`（含中国/中國 punycode）后缀优先 `default-dns`；
  - DNS 增加“命中直连规则的域名优先 `default-dns`”提示规则，减少首开慢；
  - `dns.independent_cache` 维持 `false`（避免轻微性能损失）。
