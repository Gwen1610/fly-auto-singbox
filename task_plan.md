# Task Plan: 解耦 Pipeline + 自动安装 + 内置提取器

## Goal
在 `fly-auto-singbox` 中实现三段解耦，并新增自动安装能力与内置订阅提取能力：
1) 手动安装指导（保留原下载方式，但不自动安装）；
2) 节点提取（不含分流）+ 分流构建（独立模块）；
3) `fly on/off/status/log` 后台进程管理。
4) `fly install-singbox` 自动下载并安装 Linux/mac 对应版本（当前会话仅 dry-run 验证，不实际下载）。

## Current Phase
Complete (Phase 17)

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

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| 并行 shell 写文件被审批策略拒绝 | 1 | 改用 `apply_patch` 创建/更新文件 |
| `SUDO_BIN=\"\"` 在加载默认值后被覆盖为 `sudo` | 1 | `load_env` 改为仅在变量未定义时才设置默认 sudo |
| 并行执行验证命令时单条命令被审批策略拒绝 | 1 | 拆分为单独命令执行，通过后继续 |
| `build_route_rules.py` 在最小测试环境缺少 `requests` | 1 | 增加 `urllib` 回退，不依赖第三方包也可运行 |
| 本地规则源相对路径被解析到 `config/` 下导致找不到文件 | 1 | 相对路径优先按 sources 文件目录解析，若不存在再回退到工作目录 |
