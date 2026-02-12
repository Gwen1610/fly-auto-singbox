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
