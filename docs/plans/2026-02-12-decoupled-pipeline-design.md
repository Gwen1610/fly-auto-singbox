# Decoupled Fly Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 `fly-auto-singbox` 中实现三段解耦流水线：手动安装指导、节点提取与分流构建分离、以及 sing-box 后台进程 on/off 管理。

**Architecture:** `fly` 作为统一 CLI，只做编排；节点提取和分流构建由两个独立 Python 模块实现。`sing-box-subscribe` 保持外部依赖身份，仅用于提取可用四区节点，不在 fly 仓库内修改。运行态管理使用 `nohup + pid file`，与配置生成解耦。

**Tech Stack:** Bash (`fly`), Python 3 (`scripts/extract_nodes.py`, `scripts/build_config.py`), JSON config files, POSIX process tools.

### Task 1: Define New Command Surface

**Files:**
- Modify: `fly-auto-singbox/fly`
- Create: `fly-auto-singbox/config/extract.providers.json`
- Create: `fly-auto-singbox/config/route-rules.json`

**Step 1: Rewrite command list and usage**
- Commands: `install-guide`, `extract`, `build-config`, `pipeline`, `on`, `off`, `status`, `log`.
- Remove old systemd/apply workflow from default path.

**Step 2: Add extraction/build/runtime env defaults**
- Include paths for `sing-box-subscribe` dir, intermediate nodes file, final config output, pid/log files.

**Step 3: Add default config templates**
- `extract.providers.json`: extraction-only provider input.
- `route-rules.json`: routing rule file used only by build phase.

### Task 2: Implement Extraction Module (No Routing)

**Files:**
- Create: `fly-auto-singbox/scripts/extract_nodes.py`
- Test: `fly-auto-singbox/tests/test_pipeline.sh`

**Step 1: Write failing test**
- Expect command wiring and output file existence behavior.

**Step 2: Implement extractor**
- Read extraction providers config.
- Build temporary `temp_json_data` with `Only-nodes=true` and output path to nodes file.
- Invoke `sing-box-subscribe/main.py` via subprocess.
- Validate output is JSON list with non-empty `tag`.

**Step 3: Run test for extraction path**
- Verify generated nodes JSON structure.

### Task 3: Implement Routing Build Module

**Files:**
- Create: `fly-auto-singbox/scripts/build_config.py`
- Create: `fly-auto-singbox/config/base-template.json`
- Test: `fly-auto-singbox/tests/test_pipeline.sh`

**Step 1: Write failing test**
- Build from sample nodes and assert final config contains selectors + route rules.

**Step 2: Implement builder**
- Input: nodes JSON list + route rules JSON + base template JSON.
- Group nodes by region (US/HK/SG/JP regex).
- Build outbounds: Proxy selector, region selectors, direct, node outbounds.
- Inject route rules + final target.
- Write final config JSON.

**Step 3: Run tests**
- Ensure config includes expected tags and routes.

### Task 4: Implement Runtime Module (on/off/status/log)

**Files:**
- Modify: `fly-auto-singbox/fly`
- Test: `fly-auto-singbox/tests/test_pipeline.sh`

**Step 1: Write failing test**
- Idempotency behaviors: repeated `on` and `off` outputs.

**Step 2: Implement commands**
- `on`: check config -> check pid -> `sudo -v` -> `sudo nohup sing-box run -c ...` -> write pid.
- `off`: kill pid -> fallback `pkill -f` -> remove pid.
- `status`: inspect pid and process liveness.
- `log`: `tail -f` log file.

**Step 3: Ensure command idempotency**
- Duplicate `on` should not spawn new process.
- Duplicate `off` should return not running.

### Task 5: Docs, Verification, Git Push

**Files:**
- Modify: `fly-auto-singbox/README.md`
- Modify: `fly-auto-singbox/tests/test_pipeline.sh`

**Step 1: Update README to new decoupled flow**
- Manual sing-box install guide.
- 2-step config generation (extract + build-config).
- Runtime lifecycle commands.

**Step 2: Run verification**
- `bash tests/test_pipeline.sh`
- Smoke check `./fly help`
- `git status --short`

**Step 3: Commit and push**
- Commit with clear message.
- Push to `origin/main`.
