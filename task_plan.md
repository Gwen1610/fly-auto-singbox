# Task Plan: 解耦 fly sing-box pipeline

## Goal
在 `fly-auto-singbox` 中实现三段解耦：
1) 手动安装指导（保留原下载方式，但不自动安装）；
2) 基于 `sing-box-subscribe` 的节点提取（不含分流）+ 分流构建（独立模块）；
3) `fly on/off/status/log` 后台进程管理。

## Current Phase
Phase 5

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

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| 并行 shell 写文件被审批策略拒绝 | 1 | 改用 `apply_patch` 创建/更新文件 |
| `SUDO_BIN=\"\"` 在加载默认值后被覆盖为 `sudo` | 1 | `load_env` 改为仅在变量未定义时才设置默认 sudo |
