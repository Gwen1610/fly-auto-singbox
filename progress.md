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
- [ ] 提交并 push 本轮变更。
