# Task Plan: 解耦 Pipeline + 自动安装 + 内置提取器

## Goal
在 `fly-auto-singbox` 中实现三段解耦，并新增自动安装能力与内置订阅提取能力：
1) 手动安装指导（保留原下载方式，但不自动安装）；
2) 节点提取（不含分流）+ 分流构建（独立模块）；
3) `fly on/off/status/log` 后台进程管理。
4) `fly install-singbox` 自动下载并安装 Linux/mac 对应版本（当前会话仅 dry-run 验证，不实际下载）。

## Current Phase
Phase 9

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
- [ ] 提交并 push
- **Status:** in_progress

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| 并行 shell 写文件被审批策略拒绝 | 1 | 改用 `apply_patch` 创建/更新文件 |
| `SUDO_BIN=\"\"` 在加载默认值后被覆盖为 `sudo` | 1 | `load_env` 改为仅在变量未定义时才设置默认 sudo |
