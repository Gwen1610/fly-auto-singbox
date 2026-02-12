# Connectivity Defaults + urltest Regions Implementation Plan

> **For Codex:** When executing, verify by running `bash tests/test_pipeline.sh` and `sing-box check -c config.json` before claiming success.

**Goal:** Make the generator produce a `config.json` that works reliably for Safari + Google/YouTube without manual edits, and default HK/SG/JP provider subgroups to auto-pick fastest.

**Architecture:** Implement “connectivity defaults injection” inside `scripts/build_config.py` so the output config is self-contained and stable. Keep user-defined nodes and grouping strategy intact.

**Tech Stack:** Bash CLI (`fly`), Python generator (`scripts/build_config.py`), sing-box config schema.

## Tasks

### Task 1: Tests (RED)

**Files:**
- Modify: `tests/test_pipeline.sh`

**Steps:**
1. Add assertions that `B-Singapore` and `A-Japan` are `urltest`.
2. Add assertion that `A-America` remains `selector`.
3. Run `bash tests/test_pipeline.sh` and confirm it fails before implementation.

### Task 2: Generator (GREEN)

**Files:**
- Modify: `scripts/build_config.py`

**Steps:**
1. Expand `URLTEST_REGIONS` to include `Singapore` and `Japan` (leave `America` out).
2. Run `bash tests/test_pipeline.sh` and confirm it passes.

### Task 3: Docs & Closeout

**Files:**
- Create: `docs/future-work.md`
- Modify: `README.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

**Steps:**
1. Add `docs/future-work.md` to record optional next optimizations.
2. Update README to document connectivity defaults injection and default urltest regions.
3. Update planning markdown files to record what changed and verification evidence.

### Task 4: Verification & Release

**Steps:**
1. Run `bash tests/test_pipeline.sh` (expect PASS).
2. Run `sing-box check -c config.json` after `./fly build-config` (expect exit code 0).
3. `git status` is clean except local untracked artifacts (`config.json`, `cache.db`).
4. Commit and push to GitHub `origin/main`.

