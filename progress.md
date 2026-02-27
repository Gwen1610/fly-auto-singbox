# Progress

## Session 2026-02-12
- [x] 加载 `superpowers:brainstorming`。
- [x] 加载 `superpowers:writing-plans`。
- [x] 检查 `fly-auto-singbox` git 状态（干净工作区）。
- [x] 创建 `docs/plans/2026-02-12-decoupled-pipeline-design.md`。
- [x] 重置并同步 `task_plan.md/findings.md/progress.md` 到本次目标。
- [x] 实现新 `fly` 命令骨架和解耦命令面。
- [x] 新增 `scripts/extract_nodes.py`。
- [x] 新增 `scripts/build_config.py`。
- [x] 新增/调整 `config/*` 模板文件和 `.gitignore`。
- [x] 重写 README 为新架构说明。
- [x] 删除旧测试 `tests/test_fly.sh`，新增 `tests/test_pipeline.sh`。
- [x] 运行 `bash tests/test_pipeline.sh` 并通过。
- [x] 运行 `bash -n fly` 和 `python3 -m py_compile ...` 并通过。
- [x] 执行 git commit。
- [x] 执行 `git push origin main`。
- [x] 为自动安装能力新增计划文档 `docs/plans/2026-02-12-auto-install-singbox-design.md`。
- [x] 实现 `install-singbox`（linux/darwin + amd64/arm64 + version/install-dir/dry-run）。
- [x] 将 `install-guide` 调整为 `install-singbox --dry-run` 兼容别名。
- [x] 更新 README 与 `config/fly.env.example`。
- [x] 更新 `tests/test_pipeline.sh`：新增 mock releases + dry-run 安装断言。
- [x] 完成验证（语法、测试、Python 编译）。
- [x] 提交并 push 本轮变更。
- [x] 新增 `scripts/internal_subscribe/` 内置提取器实现（含 parsers + tool）。
- [x] 重写 `scripts/extract_nodes.py` 为本仓库内实现，不再调用外部目录。
- [x] 更新 `config/extract.providers.example.json` 与 `requirements.txt`。
- [x] 重写 README，补充安装校验、订阅填写位置、输出文件位置。
- [x] 跑全量验证（`bash -n fly`、`python3 -m py_compile ...`、`bash tests/test_pipeline.sh`）。
- [x] push 本轮“内置提取器”改动。
- [x] 新增 `check-singbox` 命令用于安装前检查。
- [x] `install-singbox` 增加同版本自动跳过与 `--force` 强制重装逻辑。
- [x] README 增加 `sing-box-subscribe` 原作者署名与“先检查再安装”流程。
- [x] 再次完成验证（`bash -n fly`、`python3 -m py_compile ...`、`bash tests/test_pipeline.sh`）。
- [x] 提交并 push 本轮“安装逻辑完善+署名”改动。
- [x] 放宽地区匹配规则，支持 `US01/HK01/SGP/JP` 等命名。
- [x] 为 `extract` 无匹配报错增加 sample tags 提示。
- [x] 新增兼容文件 `config_template/minimal_four_regions.json`。
- [x] 再次完成验证（`bash -n fly`、`python3 -m py_compile ...`、`bash tests/test_pipeline.sh`）。
- [x] 修复订阅 URL 误判 bug（`http/https` 不再当作节点协议前缀）。
- [x] 示例配置默认 `enabled=true`。
- [x] 再次完成验证（`bash -n fly`、`python3 -m py_compile ...`、`bash tests/test_pipeline.sh`）。
- [x] 提交并 push 本轮“extract 兼容修复”改动。
- [x] 将 `config/route-rules.json` 改为 `config/route-rules.example.json` 参考模板。
- [x] `./fly init` 支持从 `route-rules.example.json` 生成 `route-rules.json`。
- [x] 默认 route 策略调整为无分流规则（`final=Proxy`, `rules=[]`）。
- [x] README 增加 `base-template/minimal_four_regions/route-rules.example` 作用说明。
- [x] 更新 `tests/test_pipeline.sh` 默认路由断言（`route.rules` 为空）。
- [x] 完成验证（`bash -n fly`、`conda run -n yellow python -m py_compile ...`、`bash tests/test_pipeline.sh`）。
- [x] 提交并 push 本轮“route-rules 模板化 + 默认无分流”改动。
- [x] 从 `config/base-template.json` 移除全部 `geosite/geoip/rule_set` 预置策略。
- [x] 删除 `config_template/minimal_four_regions.json`，统一模板入口为 `config/base-template.json`。
- [x] 更新 README 与测试，确保默认输出不含 `geosite/geoip`。
- [x] 提交并 push 本轮“移除历史分流策略”改动。
- [x] 为 `fly` 增加基于 TTY 的彩色输出（info/warn/error/state）。
- [x] 保证非交互输出纯文本，维持脚本与测试兼容。
- [x] README 增补颜色说明与 `NO_COLOR=1` 用法。
- [x] 整理 markdown：计划文档增加 archive note。
- [x] 提交并 push 本轮“颜色输出 + markdown 收尾”改动。
- [x] 新增计划文档 `docs/plans/2026-02-12-qx-route-rules-integration-design.md`。
- [x] 集成 `build-rules` 解耦模块（`fly` + `scripts/build_route_rules.py`）。
- [x] 新增 `config/rule-sources.example.json`，`init` 自动生成 `config/rule-sources.json`。
- [x] 更新测试覆盖 `.list/.yaml/.txt` 转换链路，并验证被 `build-config` 消费。
- [x] 修复无 `requests`/无 `PyYAML` 的运行回退。
- [x] README 增加 `build-rules` 使用说明并补充 `sing-box-geosite` 署名。
- [x] 提交并 push 本轮“QX 规则转换模块集成”改动。
- [x] 新增 `manual_rules` 支持，允许直接写 QX 单行补充规则。
- [x] 新增 `Direct/Reject` 出口别名规范化与 `block` outbound 支持。
- [x] 更新示例配置，加入人工补充规则样例（含 `GEOIP,CN,Direct`）。
- [x] 更新测试覆盖 manual rules + alias 转换路径。
- [x] 完成验证（`bash -n fly`、`conda run -n yellow python -m py_compile ...`、`bash tests/test_pipeline.sh`）。
- [x] 提交并 push 本轮“manual_rules + alias 兼容”改动。
- [x] 将所有 `.example` 文件迁移到 `config_template/`。
- [x] 更新 `fly init` 模板读取路径。
- [x] 更新 README 中 `.example` 路径说明。
- [x] 完成验证（`bash -n fly`、`bash tests/test_pipeline.sh`）。
- [x] 提交并 push 本轮“模板目录统一”改动。
- [x] `extract` 注入 `__provider_tag`，用于来源分组。
- [x] `build-config` 接入 `group-strategy`，支持来源组/地区组/业务组/Proxy 四层选择器。
- [x] 新增 `config_template/group-strategy.example.json`。
- [x] `fly init` 新增 `group-strategy.json` 生成；`build-config` 强制读取该文件。
- [x] README 补充分组设计哲学和配置示例。
- [x] 更新测试覆盖 `A/B` 双订阅来源与 `Streaming/AI` 分组。
- [x] 完成验证（`bash -n fly`、`conda run -n yellow python -m py_compile ...`、`bash tests/test_pipeline.sh`）。
- [x] 提交并 push 本轮“分层分组策略”改动。

## Session 2026-02-12 (connectivity defaults + urltest regions)
- [x] 将 `HongKong/Singapore/Japan` 的来源+地区子组默认调整为 `urltest`，`America` 保持 `selector`。
- [x] `build-config` 注入连通性默认行为（sniff、hijack-dns、QUIC reject、DNS bootstrap 规则）。
- [x] 更新 `tests/test_pipeline.sh`，增加 Singapore/Japan urltest 与 America selector 的断言。
- [x] 新增 `docs/future-work.md`，整理后续优化空间。
- [x] 更新 README，补充默认连通性注入说明与 Future Work 链接。
- [x] 验证通过：`bash tests/test_pipeline.sh`、`sing-box check -c config.json`。
- [x] 提交并 push 到 `origin/main`。

## Session 2026-02-27 (交互 TUI 规划)
- [x] 调研 sing-box Clash API 全部端点与认证方式（`findings.md` 已记录）
- [x] 调研 Tide configure 交互逻辑（纯 `read --nchars 1` + 数字键选择）
- [x] 调研 Bash TUI 技术方案（纯 Bash `read -t`、fzf、gum、Python textual 横向对比）
- [x] 更新 `findings.md`：新增 sing-box API + TUI 调研结论
- [x] 更新 `task_plan.md`：新增 Phase 19-22（API 基础设施、select、delay、monitor）
- [x] 进入实现阶段并完成交互命令首版（`select/delay/monitor`）

## Session 2026-02-27 (配置生成交互化 + 终端档位)
- [x] 对齐 Claude 已落地的交互模式与命令面（`./fly help`、`README.md`、`CLAUDE.md`）。
- [x] 增加构建交互向导：`build-config --interactive` / `pipeline --interactive`（第一层 iOS/电脑端，第二层 Rule Set，有桌面第三层 VT/terminal）。
- [x] 增加 `build-rules --interactive`（Rule Set / inline 二选一）。
- [x] 新增桌面 profile 参数：`--profile vt|terminal`，默认 `vt`，并新增 `DESKTOP_PROFILE_DEFAULT`。
- [x] 新增终端配置输出：`config.terminal.json`（`--profile terminal`）。
- [x] `build_config.py` 新增 terminal profile：
  - DNS 使用 1.12+ 新 server 格式；
  - 去掉 deprecated 的 `dns.rules[].outbound=any`；
  - 最初设置 `route.default_domain_resolver=default-dns`（后续已收敛为 per-outbound `domain_resolver`）。
- [x] 更新 `config_template/fly.env.example`、`README.md`、`CLAUDE.md`、`task_plan.md`、`findings.md`。
- [x] 验证通过：
  - `bash -n fly`
  - `conda run -n yellow python -m py_compile scripts/build_config.py scripts/build_route_rules.py scripts/extract_nodes.py`
  - `bash tests/test_pipeline.sh`

## Session 2026-02-27 (fly on 交互启动 + terminal fatal 修复)
- [x] `fly on` 增加交互选配置（扫描当前目录 `*.json`），并支持 `--config` 显式指定。
- [x] 修复 terminal profile 启动 fatal（移除 direct-type DNS detour）。
- [x] terminal profile 的 `clash_mode=direct` 对齐回 `default-dns`，避免落回 `system-dns` 造成 DNS 行为偏移。
- [x] 新增统一入口 `fly interactive` / `fly menu`，可在单界面选择提取节点/生成规则/构建配置/一键流水线。
- [x] 终端 profile 保持原有能力：分层分组、route 注入、CN 规则联动不变。
- [x] README / CLAUDE.md 补充 `fly on` 交互与 `--config` 用法。
- [x] 补充测试断言：terminal profile 不再输出 direct detour，且保留关键 route 规则。

## Session 2026-02-23 (bulianglin 配置借鉴分析，文档先行)
- [x] 阅读用户提供的 `example/config.json` 与 `example/tun.json`，提取 DNS 防泄露相关逻辑。
- [x] 尝试读取原教程页面，确认被 Cloudflare 验证拦截（无法自动抓正文）。
- [x] 对照当前 VT 1.11.4 兼容生成配置，归纳“已做到 / 可借鉴 / 不建议照搬”的点。
- [x] 新增文档 `docs/bulianglin-dns-leak-borrowing-notes.md`（仅方案思路，不改代码）。

## Session 2026-02-27 (配置目录统一 + terminal DNS 防泄露对齐)
- [x] `fly` 默认输出目录切换到 `CONFIG_OUTPUT_DIR=./runtime-configs`，并派生 `CONFIG_JSON/IOS/TERMINAL`。
- [x] `fly on` 交互选择改为扫描 `runtime-configs/*.json`（可选自定义文件名）。
- [x] `fly on --config <basename>` 支持优先从 `runtime-configs/` 解析（无需写完整路径）。
- [x] terminal profile DNS 对齐 VT 防泄露语义：`google` server 明确 `detour=Proxy`。
- [x] terminal profile 从全局 `route.default_domain_resolver` 调整为按出站注入 `domain_resolver`（减少行为偏移）。
- [x] 更新文档：`README.md`、`CLAUDE.md`、`docs/claude-code-handoff.md`、`config_template/fly.env.example`。
- [x] 验证通过：
  - `bash -n fly`
  - `conda run -n yellow python -m py_compile scripts/build_config.py scripts/build_route_rules.py scripts/extract_nodes.py`
  - `bash tests/test_pipeline.sh`
  - `./fly build-config --target desktop --profile terminal --ruleset`

## Session 2026-02-27 (terminal DNS 泄露加固：macOS guard + proxy-mode 解析)
- [x] macOS DNS guard：选择“当前有 IP 的网络服务”，并把系统 DNS 指向 tun 网段内地址（fail-closed，IPv6 不可用时回退 IPv4-only），避免 LAN 私网 DNS 绕过 tun 导致泄露。
- [x] macOS DNS guard：应用/恢复后 flush DNS cache（`dscacheutil` + `mDNSResponder`）。
- [x] macOS DNS guard：可选启动 root watchdog，sing-box 异常退出时也能自动恢复系统 DNS（避免残留）。
- [x] terminal profile：注入 `mixed-in` 的 `route.rules[].action=resolve`，代理模式下 DNS 统一走 sing-box DNS 路由。
- [x] terminal profile：tun 入站默认 `sniff_override_destination=false`（减少额外“域名覆盖”触发的解析链路）。
- [x] 更新 `tests/test_pipeline.sh` 覆盖上述行为。
