# Claude Code 交接文档（2026-02-27 晚间）

> 用途：这份文档是 Codex -> Claude Code 的工作交接，覆盖当前项目能力、目录结构、未提交改动、以及当前仍未解决的问题。  
> 范围：仅基于本地仓库现状，不包含用户隐私订阅内容。

---

## 1) 项目目标与当前定位

### 项目目标
`fly-auto-singbox` 的目标是：通过 `./fly` 一套命令，把以下流程打通并自动化：
1. 订阅提取（节点提取）
2. QX/Clash 规则转换（inline 或 rule-set）
3. sing-box 配置生成（iOS / 桌面、VT / terminal 档位）
4. 运行管理与交互运维（on/off/log/select/delay/monitor）

### 当前兼容重点
- **首要兼容目标：VT 核心 1.11.4（iOS + 桌面）**
- 同时维护桌面 terminal 档位（本机环境校验为 `sing-box 1.12.21`）

---

## 2) 当前已实现功能（按命令面）

以 `./fly help` 为准，当前主命令如下：

### 初始化与环境
- `./fly init [--force]`
- `./fly check-singbox`
- `./fly install-singbox ...`
- `./fly install-guide`

### 规则与配置构建
- `./fly build-rules [--ruleset] [--interactive] ...`
- `./fly build-ruleset ...`（`build-rules --ruleset` 别名）
- `./fly publish-ruleset [--dry-run]`
- `./fly extract`
- `./fly build-config [--target desktop|ios] [--profile vt|terminal] [--ruleset] [--interactive]`
- `./fly pipeline [...]`
- `./fly interactive` / `./fly menu`（统一交互入口）

### 运行态管理
- `./fly on [--config path] [--interactive]`
- `./fly off`
- `./fly status`
- `./fly log [-n lines] [--level ...] [--no-follow] [--interactive]`
- `./fly select [group-name]`（Clash API 动态切组）
- `./fly delay [group-name]`（Clash API 延迟测试）
- `./fly monitor`（实时面板）

### 已落地的交互能力（关键）
- `build-rules/build-config/pipeline` 支持 `--interactive`
- `fly on` 支持在 `runtime-configs/*.json` 内交互选择配置
- `fly log` 支持交互选择日志等级
- `build-rules --ruleset` 在交互模式下可直接询问是否执行 `publish-ruleset`

---

## 3) 核心实现与逻辑说明

## 3.1 配置生成器：`scripts/build_config.py`
- 根据 `nodes + route-rules + base-template + group-strategy` 生成最终配置
- 输出目标：
  - `runtime-configs/config.json`（桌面 VT）
  - `runtime-configs/config.terminal.json`（桌面 terminal）
  - `runtime-configs/config.ios.json`（iOS VT）
- 关键注入逻辑：
  - `route` 基础规则注入（hijack-dns / QUIC reject / 私网直连等）
  - DNS 连通性与防泄露策略注入（参考 Bulianglin 思路）
  - 出站分组与默认策略注入（America/HongKong/Singapore/Japan + 业务组）

## 3.2 规则构建器：`scripts/build_route_rules.py`
- 从 QX/Clash 规则源构建 sing-box route 规则
- 支持两种输出：
  - inline：`config/route-rules.json`
  - ruleset：`config/route-rules.ruleset.json` + `ruleset/*.json/*.srs`
- 已修复的重要语义问题：
  - 不再把 `domain_suffix + ip_cidr` 混合在同一条 rule（避免 AND 误匹配）
  - 改为按 matcher 拆分，保持 QX/Clash 的 OR 语义

## 3.3 运行入口：`fly`
- 命令编排层（init / build / run / publish / interactive）
- 规则构建后增加了 `publish-ruleset` 引导和交互确认
- 运行时支持 macOS DNS guard（避免系统 DNS 绕过）

---

## 4) 当前目录结构（接手时建议先熟悉）

```text
.
├── fly                        # 主入口脚本
├── scripts/
│   ├── build_config.py        # 配置生成核心
│   ├── build_route_rules.py   # 规则转换核心
│   ├── extract_nodes.py       # 节点提取
│   └── internal_subscribe/    # 内置订阅解析器
├── config/                    # 运行态配置（本地编辑）
├── config_template/           # init 模板
├── runtime-configs/           # 最终配置输出目录
├── ruleset/                   # .srs 产物目录
├── docs/
│   ├── claude-code-handoff.md # 本交接文档
│   ├── bulianglin-dns-leak-borrowing-notes.md
│   ├── future-work.md
│   └── plans/
├── tests/
│   └── test_pipeline.sh       # 主回归测试
├── README.md
├── CLAUDE.md
├── task_plan.md
├── findings.md
└── progress.md
```

> 注意：`example/` 目录存在用户本地参考配置，可能含敏感信息；不应推送到远端。

---

## 5) 当前工作区状态（未提交改动）

当前 `git status --short`：
- `M findings.md`
- `M fly`
- `M progress.md`
- `M scripts/build_config.py`
- `M scripts/build_route_rules.py`
- `M task_plan.md`
- `M tests/test_pipeline.sh`
- `?? example/`

### 这批未提交改动的核心内容

1) `scripts/build_route_rules.py`
- 修复 inline/ruleset 模式的 matcher 混合问题（拆分规则块）

2) `fly`
- `build-rules --ruleset` 完成后新增提示：建议执行 `./fly publish-ruleset`
- 交互模式下可直接确认是否立即发布 ruleset

3) `scripts/build_config.py`（当前正在调试阶段，重点）
- 新增 mixed matcher 规则自动拆分（兼容旧 route-rules）
- direct 规则归一化路径有调整（`action/outbound` 归一）
- 新增 `route` 前置 `{"action":"sniff"}`
- 新增/调整 DNS：
  - `reverse_mapping = true`
  - `independent_cache = false`
  - `sniff_override_destination` 当前统一为 `true`

4) `tests/test_pipeline.sh`
- 回归测试已同步更新并通过（含 direct 规则归一化后的断言）

---

## 6) 已完成验证（当前本地）

本地最近验证结果：
- `bash -n fly` ✅
- `conda run --no-capture-output -n yellow python -m py_compile scripts/build_config.py` ✅
- `bash tests/test_pipeline.sh` ✅
- `./fly build-config --target desktop --profile vt` ✅
- `./fly build-config --target desktop --profile terminal` ✅
- `./fly build-config --target ios` ✅
- `sing-box check -c runtime-configs/config.terminal.json` ✅（无 warn）
- `sing-box check -c runtime-configs/config.json` ⚠️（在本机 1.12 环境下有 legacy DNS deprecation 提示；目标 VT 1.11.4 仍需保留旧格式）

---

## 7) 当前未解决问题（重点）

## 问题描述
用户反馈：终端运行日志里，国内站（B 站/小红书/知乎相关）仍大量走代理，不符合预期 direct。

## 复现证据（来自最新 `sing-box.log`）
示例：
- `23:30:45`，`45.116.82.51:443` -> `outbound/shadowsocks`
- `23:31:06`，`8.217.248.128:443` -> `outbound/shadowsocks`
- `23:30:44`，`103.151.151.5:443` -> `outbound/shadowsocks`

同时可见 DNS 已解析出相关域名（如 `data.bilibili.com`、`edith.xiaohongshu.com`），但后续连接仍未稳定命中 direct。

## 已做但未最终闭环的排查
1. 规则层面  
- 已确认 direct 规则本身存在（domain_suffix / ip_cidr / rule_set）
- 已确认 mixed matcher AND 问题已修复

2. 生成层面  
- 已尝试 `sniff + reverse_mapping + 缓存策略` 调整
- 已将 direct 归一到显式 `outbound: "dns_direct"`（direct-type outbound）

3. 日志层面  
- 仍观察到国内目标 IP 出站走 `shadowsocks`
- 说明“规则存在”≠“运行态命中”

## 当前判断（供 Claude 接手）
- 问题更像是**运行态命中链路问题**，不是单纯规则文本缺失：
  - 域名到连接的映射时机/范围可能不稳定
  - 某些连接在路由判定时仍只有 IP 信息
  - `geoip-cn` 命中覆盖是否不足也需要二次确认

---

## 8) Claude Code 接手建议（按优先级）

1. **先锁定“哪条规则最终命中”**
- 用最小场景复现（只访问 bilibili/xiaohongshu）
- 提升日志粒度，确认每条关键连接在 route 判定阶段的 matcher 命中链

2. **对拍配置差异**
- 对比“可用基准配置”与当前生成配置（结构层面，不要提交敏感文件）
- 聚焦：`inbounds.sniff*`、`dns.reverse_mapping`、`dns.rules`、`route.rules` 顺序与动作

3. **验证 rule_set 与 geoip 覆盖**
- 验证 `geoip-cn` 对问题 IP 是否命中
- 若未命中，确认是否应依赖域名规则兜底，或新增更稳的 IP/ASN 兜底策略

4. **保持双端一致性**
- 任何变更必须同时验证：
  - `runtime-configs/config.json`（VT）
  - `runtime-configs/config.terminal.json`（terminal）
  - `runtime-configs/config.ios.json`（iOS）

5. **改完后最小验收**
- `bash tests/test_pipeline.sh`
- `./fly build-config --target desktop --profile terminal`
- 真实访问国内站点 + `./fly log` 复核是否仍落到 `shadowsocks`

---

## 9) 外部资料入口（优先顺序）

1. 官方文档优先：
- `https://sing-box.sagernet.org/`
- `https://sing-box.sagernet.org/migration/`
- `https://sing-box.sagernet.org/configuration/route/rule_action/`
- `https://sing-box.sagernet.org/configuration/dns/`

2. 社区思路参考：
- `https://bulianglin.com/archives/singbox.html`
- `https://blog.rewired.moe/post/sing-box-config/`
- 本仓库分析：`docs/bulianglin-dns-leak-borrowing-notes.md`

---

## 10) 安全与提交注意事项

- 禁止提交任何含用户订阅信息的文件（尤其 `example/` 下私有样例）。
- `publish-ruleset` 会触发 commit + push，执行前确认远端凭据与内容安全。
- 若要提交本轮修复，建议先单独提交“规则语义修复”和“direct 命中修复”，避免混杂。
