# Task Plan: 解耦 Pipeline + 自动安装 + 内置提取器 + 交互 TUI

## Goal（当前）
为 `fly-auto-singbox` 增加终端交互 TUI 能力，实现：
1. `fly select` — 运行时动态切换出站节点（无需重启，通过 Clash API）；
2. `fly delay` — 节点延迟测试（调用 Clash API 批量或单组测速）；
3. `fly monitor` — 实时监控面板（流量统计、当前选择、延迟历史，Bash TUI）；
4. 基础能力：在 `config/base-template.json` 中注入 `experimental.clash_api` 配置。

## Current Phase
Complete (Phase 25)

## Previous Goal（已完成，Phase 1-17）
三段解耦 Pipeline + 自动安装 + 内置订阅提取器 + 分层分组 + 连通性默认注入

## Phases

### Phase 1: Planning & Baseline
- [x] 检查 git 状态和远程
- [x] 生成实现计划文档
- **Status:** complete

### Phase 2: Decoupled Pipeline Implementation
- [x] 重写 `fly` 命令编排层
- [x] 实现 `extract_nodes.py`
- [x] 实现 `build_config.py`
- [x] 新增默认配置模板
- **Status:** complete

### Phase 3: Runtime Management
- [x] 实现 `on/off/status/log`
- [x] 完成幂等行为处理
- **Status:** complete

### Phase 4: Validation & Documentation
- [x] 更新 README
- [x] 更新/重写测试
- [x] 运行验证命令
- **Status:** complete

### Phase 5: Git Delivery
- [x] 提交变更
- [x] push 到 `origin/main`
- **Status:** complete

### Phase 6: Auto Install Extension
- [x] 新增自动安装设计文档
- [x] 实现 `install-singbox`
- [x] 更新测试与 README
- [x] 验证并 push
- **Status:** complete

### Phase 7: Internalize Subscription Extractor
- [x] 内置解析器代码到本仓库
- [x] 去除 `extract` 对外部目录依赖
- [x] 更新 README 必要信息与测试
- [x] 提交并 push
- **Status:** complete

### Phase 8: Install Logic & Attribution Polish
- [x] 增加 `check-singbox` 命令
- [x] 安装前检查已有版本并支持自动跳过/`--force`
- [x] README 增加作者署名与更完整的必要操作说明
- [x] 提交并 push
- **Status:** complete

### Phase 9: Extract Compatibility Fix
- [x] 放宽 US/HK/SG/JP 匹配规则（支持 US01/HK01/SGP/JP 等）
- [x] `extract` 失败时输出 sample tags 辅助排查
- [x] 补充 `config_template/minimal_four_regions.json` 兼容文件
- [x] 提交并 push
- **Status:** complete

### Phase 10: Route Rules Template & Default No-Split
- [x] 将 `config/route-rules.json` 改为 `config/route-rules.example.json` 参考模板
- [x] `./fly init` 默认生成 `config/route-rules.json`（无分流，`final=Proxy`）
- [x] README 补充 `base-template` / `minimal_four_regions` / `route-rules.example` 作用说明
- [x] 更新测试断言，默认校验 `route.rules=[]`
- [x] 提交并 push
- **Status:** complete

### Phase 11: Remove Legacy Strategy From Base Template
- [x] 从 `config/base-template.json` 移除所有 `geosite/geoip/rule_set` 相关策略
- [x] 删除 `config_template/minimal_four_regions.json`，仅保留单一模板
- [x] README 与测试同步“无预置分流策略”行为
- [x] 提交并 push
- **Status:** complete

### Phase 12: CLI Color Output + Markdown Cleanup
- [x] 为 `fly` 增加按终端能力自动启停的彩色输出
- [x] 保持非交互输出纯文本，确保脚本解析兼容
- [x] README 补充颜色行为与关闭方式
- [x] 整理 markdown（计划文档加归档说明）
- [x] 提交并 push
- **Status:** complete

### Phase 13: Integrate QX Rule Conversion Module
- [x] 研究 `sing-box-geosite` 规则映射逻辑并确定最小复用范围
- [x] 新增独立模块 `build-rules`，仅负责生成 `config/route-rules.json`
- [x] 增加 `config/rule-sources.example.json` 与 `init` 自动生成流程
- [x] 测试覆盖 `.list/.yaml/.txt` 规则源到 route-rules 的转换与消费
- [x] README 增加使用说明与 `sing-box-geosite` 署名
- [x] 提交并 push
- **Status:** complete

### Phase 14: Manual Rule Supplements + Outbound Alias Compatibility
- [x] 支持在 `rule-sources` 中直接写 QX 单行补充规则（`manual_rules`）
- [x] 支持 `Direct/Reject` 等策略名自动规范化（`Direct->direct`, `Reject->block`）
- [x] `build-config` 增加 `block` outbound 并兼容别名校验
- [x] 示例配置与 README 增加人工补充规则说明
- [x] 测试覆盖 `manual_rules` + `GEOIP` + `Reject` 路径
- [x] 提交并 push
- **Status:** complete

### Phase 15: Move All Example Templates to config_template
- [x] 将所有 `.example` 文件从 `config/` 迁移到 `config_template/`
- [x] 更新 `fly init` 模板路径到 `config_template/`
- [x] README 同步模板路径说明
- [x] 运行验证（`bash -n fly`、`bash tests/test_pipeline.sh`）
- [x] 提交并 push
- **Status:** complete

### Phase 16: Hierarchical Group Strategy (Source -> Region -> Business)
- [x] `extract` 保留订阅来源标识（`__provider_tag`）
- [x] `build-config` 支持按来源+地区生成子组（如 `A-HongKong`、`B-HongKong`）
- [x] 新增 `config/group-strategy.json`（来源默认、业务组、自定义 Proxy 成员）
- [x] 支持业务组（如 `Streaming`/`AI`）引用地区组并设置默认值
- [x] README 增加分组设计哲学与可配置示例
- [x] 测试覆盖双订阅来源 + 分层组生成 + 默认选择器校验
- [x] 提交并 push
- **Status:** complete

### Phase 17: Connectivity Defaults + urltest Regions
- [x] `build-config` 注入连通性默认行为（sniff、hijack-dns、QUIC reject、DNS bootstrap 规则）
- [x] `HongKong/Singapore/Japan` 的来源+地区子组默认使用 `urltest`
- [x] `America` 的来源+地区子组保持 `selector`
- [x] 更新 README 与新增 `docs/future-work.md`
- [x] 更新测试断言
- [x] 完成验证并推送到 GitHub
- **Status:** complete

---

## Phase 19: Clash API 基础设施（API Foundation）

**目标：** 在 `config/base-template.json` 中注入 `experimental.clash_api`，并在 `fly` 脚本中封装 API 调用能力，为后续所有交互命令提供底座。

### 设计决策

- **仅桌面端启用 API**：`config/base-template.json` 注入 `clash_api`；iOS 模板不改（VT 1.11.4 iOS 不需要运行时 API 交互）。
- **可配置地址与密钥**：`fly.env` 新增 `API_HOST`（默认 `127.0.0.1:9090`）和 `API_SECRET`（默认空）。
- **模板注入方式**：`experimental.clash_api` 作为固定字段写入 `config/base-template.json`；`build_config.py` 可选替换地址/密钥（从 `fly.env` 读取后通过环境变量传入）。
- **`fly api` 内部函数**：封装 `curl` 调用，处理认证头、错误码、JSON 输出，供 `select/delay/monitor` 共用。

### 任务列表

- [ ] 在 `config/base-template.json` 中新增 `experimental.clash_api`（`external_controller: "127.0.0.1:9090"`, `secret: ""`）
- [ ] 在 `config_template/fly.env.example` 新增 `API_HOST` 和 `API_SECRET`
- [ ] 在 `fly` 脚本中实现 `fly_api()` 函数（curl wrapper，支持 GET/PUT/PATCH/DELETE，返回 HTTP 状态码 + JSON body）
- [ ] 实现 `fly_api_check()` 函数：检查 API 是否可达（fly 未启动时给出友好提示）
- [ ] 更新 `tests/test_pipeline.sh`：验证生成的 `config.json` 包含 `experimental.clash_api.external_controller`
- [ ] 更新 `README.md`：新增 API 配置说明段落
- **Status:** pending

---

## Phase 20: `fly select` — 实时节点切换（Tide 风格向导）

**目标：** 实现 `fly select [group]` 命令：无需重启 sing-box，通过 Clash API 动态切换 selector 出站的当前选择。交互风格参照 Tide `configure`：数字键快选 + 清屏重绘。

### 交互流程设计

```
$ ./fly select

=== fly select ===

可切换的分组：
(1) Proxy          [当前: HongKong]
(2) HongKong       [当前: A-HongKong]
(3) Streaming      [当前: HongKong]
(4) AI             [当前: HongKong]
(q) 退出

选择分组 [1-4/q]: 2

=== HongKong 节点列表 ===
(1) A-HongKong     ★ 当前  12ms
(2) B-HongKong           45ms
(b) 返回
(q) 退出

选择节点 [1-2/b/q]: 2

[fly] HongKong -> B-HongKong ✓
```

### 技术方案

- 第一步：`GET /proxies` 过滤出 `type=Selector` 的出站，排除 `GLOBAL`
- 显示分组列表 + 当前选择 + 历史延迟（来自 `history[-1].delay`）
- 用户选分组后，列出该 selector 的 `all` 列表
- 用户选节点后，`PUT /proxies/{group}` 切换
- 纯 Bash 实现：`read -rsn1` + `printf` + ANSI 着色
- 支持直传参数：`./fly select HongKong` 跳过分组选择步骤

### 任务列表

- [ ] 实现 `cmd_select()` 函数（依赖 Phase 19 的 `fly_api()`）
- [ ] 实现 `_fly_tui_title()`、`_fly_tui_option()`、`_fly_tui_menu()` 等 Tide 风格 TUI 组件（可复用）
- [ ] 处理边界情况：未运行/API 不可达、group 不存在、节点不在 selector 的 `all` 列表中
- [ ] 支持 `./fly select [group-name]` 直接指定分组跳过第一步
- [ ] 测试：mock API（`--api-host` 参数指向测试服务器）验证切换流程
- **Status:** pending

---

## Phase 21: `fly delay` — 节点延迟测试

**目标：** 实现 `fly delay [group]` 命令，调用 Clash API 对指定分组（或全部分组）的节点批量测速，并以颜色编码显示结果。

### 交互设计

```
$ ./fly delay HongKong

测试 HongKong 节点延迟...

  A-HongKong     ████  12ms   [绿色]
  B-HongKong     ████  45ms   [绿色]

$ ./fly delay

测试所有 selector 分组...

  Proxy          跳过（非直连节点）
  HongKong
    A-HongKong   12ms
    B-HongKong   45ms
  America
    A-US-01      180ms
    A-US-02      timeout
```

### 技术方案

- 单组：`GET /group/{name}/delay?url=https://www.gstatic.com/generate_204&timeout=5000`
- 响应 map `{tag: ms}`，按延迟排序后显示
- 颜色：< 100ms 绿，100-300ms 黄，> 300ms 红，timeout 红+斜体
- 无参数时遍历所有 `type=Selector` 分组
- 测速进行中显示 spinner（复用 `_fly_spin()` 函数）

### 任务列表

- [ ] 实现 `cmd_delay()` 函数
- [ ] 实现 `_fly_spin()` spinner 组件（异步后台 + kill）
- [ ] 延迟结果颜色渲染函数 `_fly_render_delay()`
- [ ] 无参数时批量遍历所有 selector 分组
- [ ] 更新 README
- **Status:** pending

---

## Phase 22: `fly monitor` — 实时监控面板

**目标：** 实现 `fly monitor` 命令，用 Bash TUI 呈现一个可实时刷新的面板，展示：sing-box 运行状态、实时流量、各 selector 分组当前选择与延迟、最近日志行。

### 面板布局设计

```
╔══════════════════════════════════════════════╗
║  fly monitor         [running]  2026-02-27   ║
╠══════════════════════════════════════════════╣
║  流量  ↑ 1.2MB/s  ↓ 3.4MB/s                 ║
╠══════════════════════════════════════════════╣
║  分组状态                                    ║
║  Proxy        → HongKong                     ║
║  HongKong     → A-HongKong   [12ms]          ║
║  Streaming    → HongKong                     ║
╠══════════════════════════════════════════════╣
║  [s] 切换节点  [d] 测延迟  [q] 退出          ║
╚══════════════════════════════════════════════╝
```

### 技术方案

- `tput smcup` 进入备用缓冲区，`trap ... rmcup` 退出时恢复
- 主循环：`read -rsn1 -t 3 key`（3 秒超时 = 自动刷新周期）
- 数据来源：
  - 运行状态：检查 PID 文件
  - 流量：`GET /traffic`（单次 HTTP，读一条 JSON 行）
  - 分组状态：`GET /proxies`（过滤 Selector，取 `now` + `history[-1].delay`）
- 按 `s` 呼出 `cmd_select()` 的分组选择子流程
- 按 `d` 呼出 `cmd_delay()` 的测速子流程
- `printf '\033[H'` 回顶重绘（非 `clear`，避免闪烁）
- JSON 解析：`python3 -c` 或纯 `grep/sed`（倾向 python3 已存在）

### 任务列表

- [ ] 实现 `cmd_monitor()` 函数
- [ ] 实现 `_fly_monitor_render()` 面板绘制（可测试）
- [ ] `GET /traffic` 的数据拉取与格式化（Bytes -> KB/MB/s）
- [ ] 集成 `select` 和 `delay` 的子流程调用（在 monitor 内嵌套使用 tui 组件）
- [ ] 终端尺寸适配（`tput cols/lines` 动态布局）
- [ ] 更新 README
- **Status:** pending

---

## Phase 19-22 状态对齐（Claude 交互升级已完成）

- [x] Clash API 基础设施（`experimental.clash_api` + `fly_api`）已落地
- [x] `fly select / fly delay / fly monitor` 已落地并进入主命令帮助
- [x] 相关 README / CLAUDE.md 已补齐交互命令说明
- [x] 关键修复已合入（`load_env` 变量读取、`fly_api` 子 shell 状态码）
- **Status:** complete

---

## Phase 23: 配置生成/规则构建交互化 + 终端内核兼容档位

**目标：** 复用现有 Tide 风格 TUI，把 `build-rules` 和 `build-config/pipeline` 做成交互式，并新增桌面端 `terminal` 兼容配置档位（面向终端 sing-box 1.12+，减少 legacy 告警）。

### 任务列表

- [x] 设计交互路径：第一层 iOS/电脑端，第二层 Rule Set/无 Rule Set，第三层（电脑端）VT/terminal
- [x] 在 `fly` 中实现 `build-rules --interactive` 与 `build-config/pipeline --interactive`
- [x] 新增 `--profile vt|terminal` 参数与 `DESKTOP_PROFILE_DEFAULT` 默认值
- [x] 新增终端输出文件路径：`config.terminal.json`
- [x] 在 `build_config.py` 增加 terminal profile（新 DNS server 格式 + resolver 迁移；后续收敛为 per-outbound `domain_resolver`）
- [x] 更新 README / CLAUDE.md / `config_template/fly.env.example`
- [x] 更新并通过 `tests/test_pipeline.sh`（覆盖 terminal profile 断言）
- **Status:** complete

---

## Phase 24: `fly on` 交互选配置 + 终端启动 fatal 修复

**目标：**
1) `fly on` 支持交互选择当前目录配置文件；  
2) 修复 terminal profile 在 1.12+ 的 `detour to an empty direct outbound makes no sense` 启动 fatal；  
3) 保持原有分组/分流/连通性逻辑不回退。

### 任务列表

- [x] 为 `fly on` 增加 `--config` / `--interactive` 参数，并默认在 TTY 下弹出配置选择
- [x] 交互菜单支持扫描当前目录 `*.json` 并选择启动文件
- [x] 修复 terminal profile 的 DNS detour 逻辑，避免 direct-detour fatal
- [x] 修正 terminal profile 的 DNS 规则对齐 VT 逻辑（`clash_mode=direct -> default-dns`）
- [x] 新增统一配置交互入口 `fly interactive/menu`（提取节点/生成规则/构建配置/一键流水线）
- [x] 增补测试断言（terminal profile 保留原有规则能力 + 无 direct detour fatal 配置形态）
- [x] 更新 README / CLAUDE.md / 进度文档说明
- **Status:** complete

---

## Phase 25: 统一配置输出目录 + 终端 DNS 防泄露对齐

**目标：**
1) 所有最终 `config*.json` 默认输出到统一目录（`runtime-configs/`）；  
2) `fly on` 只要目标文件在该目录就可被交互选择/通过 `--config` 简写名启动；  
3) terminal profile 的 DNS 行为对齐 VT 防泄露策略（仅做新内核兼容字段迁移，不退化逻辑）。

### 任务列表

- [x] 在 `fly` 中引入 `CONFIG_OUTPUT_DIR` 默认值（`./runtime-configs`）并派生 `CONFIG_JSON/IOS/TERMINAL`
- [x] `fly on` 交互改为扫描 `CONFIG_OUTPUT_DIR`，支持自定义命名 JSON
- [x] `fly on --config <basename>` 支持优先从 `CONFIG_OUTPUT_DIR` 解析
- [x] terminal DNS 配置补齐 `google` server `detour=Proxy`，保持 VT 的远程 DoH 路由意图
- [x] 更新 `config_template/fly.env.example`、`README.md`、`CLAUDE.md`、`docs/claude-code-handoff.md`
- [x] 更新并通过 `tests/test_pipeline.sh`（覆盖 `runtime-configs` 路径与 `google detour=Proxy` 断言）
- **Status:** complete

---

## Phase 26: terminal DNS 泄露加固（macOS guard + proxy-mode 解析）

**目标：**
1) 解决“终端模式仍有 DNS 泄露”的常见 macOS 场景（IPv6 resolver、VPN 启动后网络服务映射失败等）；  
2) 代理模式（`mixed-in`）下避免走系统 DNS；  
3) 保持 VT 档逻辑不回退，terminal 档继续无 deprecated warn。

### 任务列表

- [x] macOS DNS guard：选择“当前有 IP 的网络服务”（避免接口被 `utun*` 干扰导致映射失败）
- [x] macOS DNS guard：同时设置 IPv4/IPv6 公网 DNS，并在应用/恢复后 flush DNS cache
- [x] terminal profile：为 `mixed-in` 注入 `route.rules[].action=resolve`（代理模式 DNS 统一走 sing-box）
- [x] terminal profile：tun 入站默认 `sniff_override_destination=false`（减少额外解析链路）
- [x] 更新并通过 `tests/test_pipeline.sh`（新增断言覆盖）
- **Status:** complete

---

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| 并行 shell 写文件被审批策略拒绝 | 1 | 改用 `apply_patch` 创建/更新文件 |
| `SUDO_BIN=\"\"` 在加载默认值后被覆盖为 `sudo` | 1 | `load_env` 改为仅在变量未定义时才设置默认 sudo |
| 并行执行验证命令时单条命令被审批策略拒绝 | 1 | 拆分为单独命令执行，通过后继续 |
| `build_route_rules.py` 在最小测试环境缺少 `requests` | 1 | 增加 `urllib` 回退，不依赖第三方包也可运行 |
| 本地规则源相对路径被解析到 `config/` 下导致找不到文件 | 1 | 相对路径优先按 sources 文件目录解析，若不存在再回退到工作目录 |

### Phase 18: Bulianglin DNS 逻辑借鉴文档（仅分析，不改代码）
- [x] 读取 `example/config.json` / `example/tun.json`
- [x] 尝试访问教程正文（Cloudflare 验证拦截，改为基于本地拷贝分析）
- [x] 对照当前 VT 1.11.4 兼容配置，梳理已实现的防泄露能力与差距
- [x] 产出借鉴思路文档到 `docs/`
- **Status:** complete
