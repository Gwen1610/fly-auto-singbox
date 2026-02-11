# Findings & Decisions

## Requirements
- User wants an automation script project for rented Linux servers to quickly configure network proxy capability.
- Chosen proxy tool is sing-box.
- Requested output in this turn: core feature plan + implementation approach, based on deep online research.
- Research depth requirement: collect and synthesize sing-box capabilities and practical usage for this scenario.

## Research Findings
- sing-box 官方文档配置总结构包含 `log`/`dns`/`ntp`/`certificate`/`endpoints`/`inbounds`/`outbounds`/`route`/`services`/`experimental`，说明脚本应支持结构化配置生成，而不是拼接零散片段。
- 官方 CLI 提供 `sing-box check`、`sing-box format`、`sing-box merge`，非常适合自动化脚本做“配置校验 + 格式化 + 多文件合并”流水线。
- 官方 outbound 类型覆盖常见协议（如 `socks`/`http`/`shadowsocks`/`vmess`/`trojan`/`wireguard`/`hysteria2`/`vless`/`tuic` 等），可为脚本设计“协议模板化”能力。
- 文档中存在明确版本迁移变化：
  - `dns` special outbound 在 1.11.0 标记 deprecated，计划 1.13.0 移除。
  - route rule action 中 `bypass` 为 1.13.0 新增，且仅 Linux + `auto_redirect`。
  - DNS 规则中的部分字段在 1.11+/1.12+ 弃用或移除（需在脚本中做版本兼容提示）。
- 截至 2026-02-11，GitHub Releases 显示：
  - 最新稳定版（Latest）为 `1.12.20`（发布时间 2026-02-05）。
  - 最新预发布为 `1.13.0-rc.3`（发布时间 2026-02-09）。
- 通过 GitHub Releases API 复核到同样结论：
  - `1.13.0-rc.3`：`prerelease=true`，发布时间 2026-02-09。
  - `1.12.20`：`prerelease=false`，发布时间 2026-02-05。
- 迁移页显示 1.12.0/1.11.0 等版本均有配置格式演进，说明自动化脚本需要：
  - 明确支持目标主版本（建议默认锁定稳定版 1.12.x）；
  - 在导入历史配置时执行“兼容性检查与迁移提示”。
- 官方安装文档页面存在，且安装方式由多个来源构成（Distribution package / Download pre-built package / Build from source），适合脚本按“优先发行版包管理器，回退到官方预编译包”做分层策略。
- 安装细分页面显示：
  - `installation/package-manager/` 包含多平台包管理来源（如 Arch Linux、Alpine、NixOS、Homebrew、Docker image 等）。
  - `installation/download/` 提供官方预编译包下载路径。
  - `installation/build-from-source/` 提供源码构建路径。
- 说明脚本实现上应分 3 条安装通道：`pkg_manager`、`prebuilt`、`source`，并在 Linux 服务器场景优先前两者。
- CLI 命令页确认了自动化可直接利用的能力：
  - `sing-box check`：支持检查配置文件/目录，可配合 `-c`、`-C` 指定单文件或配置目录。
  - `sing-box format`：可在脚本中用于统一 JSON 配置格式。
  - `sing-box merge`：支持多文件合并为最终配置，适合模板化/分层配置管理。
- 这意味着脚本可构建“生成配置 -> merge -> format -> check -> 启动”的标准流水线，提升幂等与可调试性。
- 路由与规则集能力（`route/rule_set`）支持 `local` 与 `remote`，remote 规则集包含：
  - `url`、`format`（binary/source）、
  - `download_detour`（下载分流）、
  - `update_interval`（更新周期）。
  这非常适合自动化脚本实现“规则集订阅 + 定时更新 + 健康检查”。
- 出站管理能力可用于高可用/智能选择：
  - `selector` outbound：在多个出站间手动/策略切换。
  - `urltest` outbound：按 URL 探测延迟自动选路。
- `tun` 入站含 `auto_route` 与 `auto_redirect` 等 Linux 透明代理关键能力；结合 route rule action 的 `bypass`（1.13.0 新增）可构建更细粒度分流。
- CLI `service` 命令提供 `install`/`uninstall`/`start`/`stop`/`restart`，可直接纳入脚本，实现 system service 生命周期管理。
- provider / 订阅能力可以直接减少脚本维护成本：
  - provider 类型包括 `local`、`remote`、`default`，可把节点源与主配置解耦。
  - `remote` provider 支持 `url`、`download_detour`、`healthcheck_url`、`healthcheck_interval`、`includes`/`excludes`、`override` 等字段，适合做“自动拉取 + 过滤 + 健康检查 + 重写”。
- GitHub README 的能力描述强调：
  - 支持 shadowsocks、hysteria、tuic、vless、vmess、trojan、ssh、wireguard 等协议；
  - 内置可定制网络栈，支持 TUN + gVisor，且在 Linux 支持 netfilter 转发；
  - 支持 TProxy/Redirect/TUN 透明代理，适合服务器级流量接管场景。
- 官方 README 明确给出典型命令工作流：
  - `sing-box check -c config.json`
  - `sing-box format -w -c config.json`
  - `sing-box run -c config.json`
  - `sing-box version`
  与自动化脚本流水线高度匹配，可直接映射为预检、格式化、启动、版本校验步骤。

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Scope this turn to planning/design, not full implementation | Matches explicit user request |
| Favor bash-based automation with config templating and strict validation | Best fit for Linux server bootstrap use case |
| Default installation target: latest stable (non-prerelease) sing-box | Better production stability on rented Linux servers |
| Enforce deploy pipeline `merge -> format -> check -> service restart` | Directly leverages official CLI for deterministic deployments |
| Treat provider/rule-set as first-class inputs | Reduces manual config churn and improves long-term maintainability |
| Implement rendering with embedded Python | Removes hard dependency on `jq` for clean servers |
| Keep `apply --dry-run` as first-class path | Lets users validate generated config before privileged deploy |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Skill alias `planning-with-files` not directly resolvable by loader | Loaded with full name shown by skill list |
| GitHub CLI token invalid for account `Gwen1610` | Need `gh auth login -h github.com` before remote push |

## Resources
- sing-box GitHub: https://github.com/SagerNet/sing-box
- 配置总览: https://sing-box.sagernet.org/configuration/
- Outbound 列表: https://sing-box.sagernet.org/configuration/outbound/
- Route Rule Action: https://sing-box.sagernet.org/configuration/route/rule_action/
- DNS outbound 弃用说明: https://sing-box.sagernet.org/configuration/outbound/dns/
- Migration 总览: https://sing-box.sagernet.org/migration/
- Releases: https://github.com/SagerNet/sing-box/releases
- Installation: https://sing-box.sagernet.org/installation/
- Package manager install: https://sing-box.sagernet.org/installation/package-manager/
- Pre-built download: https://sing-box.sagernet.org/installation/download/
- Build from source: https://sing-box.sagernet.org/installation/build-from-source/
- Command 总览: https://sing-box.sagernet.org/command/
- check 命令: https://sing-box.sagernet.org/command/check/
- format 命令: https://sing-box.sagernet.org/command/format/
- merge 命令: https://sing-box.sagernet.org/command/merge/
- route rule-set: https://sing-box.sagernet.org/configuration/route/rule_set/
- selector outbound: https://sing-box.sagernet.org/configuration/outbound/selector/
- urltest outbound: https://sing-box.sagernet.org/configuration/outbound/urltest/
- tun inbound: https://sing-box.sagernet.org/configuration/inbound/tun/
- service 命令: https://sing-box.sagernet.org/command/service/
- service install: https://sing-box.sagernet.org/command/service/install/
- Provider 总览: https://sing-box.sagernet.org/configuration/provider/
- remote provider: https://sing-box.sagernet.org/configuration/provider/remote/
- GitHub README: https://github.com/SagerNet/sing-box
- GitHub README（raw）: https://raw.githubusercontent.com/SagerNet/sing-box/dev-next/README.md
- GitHub Releases API: https://api.github.com/repos/SagerNet/sing-box/releases

## Visual/Browser Findings
- 第一轮搜索完成，核心收获集中在：
  - 配置结构与 CLI 命令适合脚本化验证流程；
  - 版本迁移频繁，需要脚本内置“版本检测 + 配置兼容检查”；
  - Linux 特性（如 `bypass` + `auto_redirect`）适合作为可选增强而非默认路径。
- 第二轮页面打开后确认：
  - 版本双轨明显（稳定 1.12.x + 预发布 1.13.0-rc），项目规划应避免直接默认追 pre-release；
  - 迁移文档内容较多，配置字段变更是长期风险点，脚本需在 `check` 前后增加“版本-配置匹配”检查提示。
- 后续页面确认了“可自动化利用”的关键对象：
  - 规则集远程订阅字段（含更新间隔）；
  - selector/urltest 的多线路编排能力；
  - tun/auto_route/auto_redirect 的 Linux 透明代理能力；
  - service 子命令可直接用于守护进程管理。
- provider 页面补充了“可运维化”的要点：
  - 远程订阅源支持健康检查与字段覆写；
  - 可通过 includes/excludes 在脚本层做节点白名单/黑名单；
  - 与 selector/urltest 结合后，可做全自动线路管理。

## Proposed Core Features (for automation project)
- Environment preflight: detect OS/arch, privilege level, and key networking prerequisites.
- Install manager: fallback chain `pkg_manager -> prebuilt -> source`.
- Version manager: stable/pre-release policy, explicit pin, and checksum verification.
- Config assembler: generate base config + fragments and compose with `sing-box merge`.
- Config validator: `sing-box format -w` then `sing-box check`.
- Secret handling: separate secret injection and permission hardening (`chmod 600`).
- Service lifecycle: `sing-box service install/start/restart/status/uninstall`.
- Health checks: process/port checks + egress test URL + optional provider health probes.
- Rule/provider updater: support remote `rule_set` / `provider` with update intervals.
- Rollback & recovery: snapshot previous binary/config and auto rollback on failed deploy.
- Diagnostics bundle: collect version/config hash/log excerpts/system info for troubleshooting.

## Implementation Blueprint (high-level)
- Stack:
  - Primary: Bash for broad Linux compatibility.
  - Optional helper: Python only if JSON templating complexity requires it.
- Suggested structure:
  - `bin/sbx-bootstrap` (entrypoint)
  - `lib/preflight.sh`, `lib/install.sh`, `lib/config.sh`, `lib/service.sh`, `lib/verify.sh`, `lib/rollback.sh`
  - `templates/config/base.json`, `templates/inbound/*.json`, `templates/outbound/*.json`
  - `state/` for backups, metadata, and last-known-good pointers
- Execution flow:
  1. Preflight and input validation
  2. Resolve and install target version
  3. Render fragments then `merge -> format -> check`
  4. Install/update service and restart
  5. Run health checks
  6. On failure, rollback and emit diagnostics
- Idempotency strategy:
  - Compare desired config hash + target version to current state.
  - Skip restart when effective state does not change.
  - Keep at least one previous known-good snapshot.
