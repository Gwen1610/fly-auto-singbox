# Claude Code 接手文档（2026-02-27 快照）

## 1. 项目目标（一句话）

`fly-auto-singbox` 的目标是：用 `./fly` 一套命令，把“订阅提取 + QX/Clash 规则转换 + sing-box 配置生成 + 运行管理”串成稳定流程，重点兼容 sing-box VT `1.11.4`（桌面与 iOS）。

---

## 2. 当前状态（接手前先看）

- 当前分支：`main`
- 当前基线提交：`6ebf589`（`fix: fly_api subshell bug — FLY_API_HTTP_CODE lost when called via $()`）
- 最近核心演进：
  - `a029533`：新增交互命令 `fly select / fly delay / fly monitor`
  - `2f4c39f`：修复交互命令未加载 `fly.env` 的变量错误
  - `6ebf589`：修复 `fly_api` 子 shell 场景下状态码丢失
  - （working tree）新增构建交互向导：`build-rules/build-config/pipeline --interactive`
  - （working tree）新增桌面配置档位：`--profile vt|terminal` + `runtime-configs/config.terminal.json`
  - （working tree）`fly on` 支持交互选择 `CONFIG_OUTPUT_DIR`（默认 `runtime-configs/`）内配置文件（或 `--config` 显式指定）
  - （working tree）新增统一入口：`./fly interactive`（提取/规则/构建/流水线）
  - `8de7388`：默认生成 VT `1.11.4` 可用配置
  - `5c0e3da`：切到 Bulianglin 风格 DNS 模式
  - `1342e80`：补充 CN DNS / route 联动
- 已通过的关键验证（此前会话）：
  - `bash tests/test_pipeline.sh`
  - `./fly build-config`
  - `./fly build-config --target ios`

---

## 3. 工作目录索引（高优先级文件）

### 3.1 CLI 入口

- `fly`：主入口（命令编排、环境变量加载、启动/停止、ruleset 发布、交互命令）

### 3.2 核心脚本

- `scripts/extract_nodes.py`
  - 订阅读取与节点提取（只提 US/HK/SG/JP）
  - 输出：`build/nodes.json`
- `scripts/build_route_rules.py`
  - QX/Clash 规则转换
  - 支持两种模式：
    1) 内联规则输出 `config/route-rules.json`
    2) ruleset 输出 `config/route-rules.ruleset.json` + `ruleset/*.srs`
- `scripts/build_config.py`
  - 把节点与路由规则注入模板
  - 生成：
    - 桌面：`runtime-configs/config.json`
    - 桌面（终端）：`runtime-configs/config.terminal.json`
    - iOS：`runtime-configs/config.ios.json`
  - 内含 VT 1.11.4 与 terminal 1.12+ 双兼容分支（DNS / route 注入差异）

### 3.3 运行时配置（本地可编辑）

- `config/fly.env`
- `config/extract.providers.json`
- `config/rule-sources.json`
- `config/group-strategy.json`
- `config/route-rules.json` / `config/route-rules.ruleset.json`
- `config/base-template.json`（桌面模板）
- `config/base-template.ios.json`（iOS 模板）

### 3.4 模板目录（初始化来源）

- `config_template/*.example*`
  - `./fly init` 会从这里生成 `config/*.json` 运行时文件

### 3.5 文档目录

- `README.md`：用户主说明（命令与配置使用）
- `docs/future-work.md`：后续可优化点
- `docs/bulianglin-dns-leak-borrowing-notes.md`：Bulianglin DNS 逻辑借鉴分析
- `docs/plans/*.md`：历史设计方案与阶段说明
- `task_plan.md` / `findings.md` / `progress.md`：长期工作轨迹

### 3.6 测试

- `tests/test_pipeline.sh`：当前唯一主测试，覆盖初始化/提取/规则转换/构建主链路

---

## 4. 当前能力边界（必须知道）

1. 默认目标核心是 VT `1.11.4`，不是 sing-box 最新迁移格式。  
2. `--target desktop` 与 `--target ios` 都需要保持可运行，不允许只修一端。  
3. QX 规则链路仍保留，且支持 ruleset 模式（`--ruleset`）来降低配置体积。  
4. `example/` 下有用户本地示例文件，仅作参考，不应进入公开仓库。  

---

## 5. 快速上手（Claude Code 建议执行顺序）

1. `git status --short` 先看工作区是否干净。  
2. `./fly help` 熟悉命令面。  
3. 先跑最小验证：
   - `bash tests/test_pipeline.sh`
4. 再按目标端单独构建：
   - `./fly build-config`
   - `./fly build-config --target ios`
   - `./fly build-config --target desktop --profile terminal`
5. 如涉及 ruleset 流程，再补：
   - `./fly build-rules --ruleset`
   - `./fly build-config --ruleset`
6. 若需交互式构建：
   - `./fly build-rules --interactive`
   - `./fly build-config --interactive`
   - `./fly pipeline --interactive`
7. 运行态交互能力可单独验证：
   - `./fly select`
   - `./fly delay`
   - `./fly monitor`
8. 启动时可选配置文件：
   - `./fly on`（TTY 下交互选 `runtime-configs/*.json`）
   - `./fly on --config config.terminal.json`

---

## 6. 已知风险与排查抓手

- 若出现 `dns.servers[0].type unknown field "type"`，通常是 iOS/VT 1.11.4 兼容格式被写成了新格式。  
- 若出现 `outbound detour not found: direct`，通常是 DNS 规则指向了不存在的 outbound tag。  
- 若 ruleset 拉取 404，优先检查：
  - `RULESET_BASE_URL` 是否正确
  - `./fly publish-ruleset` 是否实际 push 成功
  - 仓库分支与路径是否为 `main/ruleset/*.srs`

---

## 7. 接手建议（下一阶段）

- 保持“能运行优先”：先保证 `./fly build-config` 产物可直接导入并启动，再考虑结构优化。  
- 对 DNS / route 修改时，桌面与 iOS 逻辑必须同时审阅，避免一端修复另一端回归。  
- 若要迁移到 sing-box `1.12+` / `1.13+` 新格式，建议做“版本开关”而不是直接替换当前 VT `1.11.4` 分支。  

---

## 8. 外部资料导航（Claude Code 查资料入口）

> 原则：**官方文档优先，社区文章用于思路借鉴**。  
> 如果两者冲突，以官方文档 + 当前目标核心版本（本项目默认 VT `1.11.4`）为准。

### 8.1 官方文档（优先级最高）

- 文档首页（总入口）：  
  `https://sing-box.sagernet.org/`
- Migration（版本迁移总入口，先看这个）：  
  `https://sing-box.sagernet.org/migration/`
- 你当前最相关的迁移章节：
  - Legacy special outbounds 迁移（1.11）：  
    `https://sing-box.sagernet.org/migration/#migrate-legacy-special-outbounds-to-rule-actions`
  - Geosite -> rule-sets 迁移（1.8，后续版本持续相关）：  
    `https://sing-box.sagernet.org/migration/#migrate-geosite-to-rule-sets`
  - 新 DNS server 格式（1.12）：  
    `https://sing-box.sagernet.org/migration/#migrate-to-new-dns-server-formats`
  - outbound DNS rule item -> domain_resolver（1.12）：  
    `https://sing-box.sagernet.org/migration/#migrate-outbound-dns-rule-items-to-domain-resolver`
- 配置参考（按模块查）：
  - Route Rule Actions：`https://sing-box.sagernet.org/configuration/route/rule_action/`
  - DNS：`https://sing-box.sagernet.org/configuration/dns/`
  - DNS Server（新格式）：`https://sing-box.sagernet.org/configuration/dns/server/`
  - Legacy DNS Server（旧格式兼容说明）：`https://sing-box.sagernet.org/configuration/dns/server/legacy/`
  - Rule Set：`https://sing-box.sagernet.org/configuration/rule-set/`
  - TUN Inbound：`https://sing-box.sagernet.org/configuration/inbound/tun/`
- Deprecated 清单（看未来会被移除什么）：  
  `https://sing-box.sagernet.org/deprecated/`
- Apple 客户端文档入口（iOS/macOS）：  
  `https://sing-box.sagernet.org/clients/apple/`

### 8.2 社区资料（用于借鉴逻辑，不直接照搬）

- Bulianglin 教程（你提供）：  
  `https://bulianglin.com/archives/singbox.html`  
  备注：该站常有 Cloudflare 校验；自动抓取失败时，优先看本仓库本地样例与分析文档。
- Rewired 配置文章（你提供，作者已标注 1.12 思路）：  
  `https://blog.rewired.moe/post/sing-box-config/`
- 对应本仓库内的借鉴分析：  
  `docs/bulianglin-dns-leak-borrowing-notes.md`

### 8.3 对 Claude Code 的检索顺序（建议）

1. 先读本仓库文档：`README.md` + `docs/claude-code-handoff.md` + `docs/bulianglin-dns-leak-borrowing-notes.md`。  
2. 再查官方 `migration` 对应版本差异，确认字段是否适配 VT `1.11.4`。  
3. 最后查社区文章，仅提炼“设计逻辑”（DNS 分层、rule_set 组织、模式切换），不要直接整段复制配置。  
4. 每次改动后都回到本项目命令验证：`bash tests/test_pipeline.sh`、`./fly build-config`、`./fly build-config --target ios`。  

### 8.4 用户历史提供的本地参考（可能不在 Git）

- `example/m78.config`：用户订阅参考配置（可能包含敏感订阅信息，禁止提交到远端）。  
- `example/correct.json`：已验证可运行的基准配置（用于对拍生成结果）。  
- `example/config.json` / `example/tun.json`：来自 Bulianglin 文章的本地拷贝，用于逻辑借鉴。  
- 如果以上文件在当前工作区不存在，说明未同步到此环境；此时按 `8.1` 官方文档 + `8.2` 社区公开文章继续推进。  
