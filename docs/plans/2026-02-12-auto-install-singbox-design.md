# Auto Install Sing-box Implementation Plan

> Archive note (2026-02-12): this is an implementation plan snapshot. For current behavior, use `README.md`.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 `fly` 增加可自动下载并安装 sing-box 的命令，支持 Linux/macOS，对本地开发机仅做 dry-run 测试不实际下载。

**Architecture:** 在 `fly` 中新增 `install-singbox` 子命令，解析系统平台和架构，基于 GitHub Releases 元数据解析目标资产 URL；执行模式下载并安装，dry-run 模式仅打印计划动作。保留 `install-guide` 作为兼容别名（走 dry-run）。

**Tech Stack:** Bash, curl, tar, install, python3(JSON parsing)

### Task 1: CLI 扩展

**Files:**
- Modify: `fly-auto-singbox/fly`

**Steps:**
1. 在 usage 中新增 `install-singbox`。
2. 实现 `install-singbox` 参数：`--version` `--os` `--arch` `--install-dir` `--dry-run` `--releases-json`。
3. 增加资产解析逻辑并接入 main dispatch。

### Task 2: 安装执行逻辑

**Files:**
- Modify: `fly-auto-singbox/fly`
- Modify: `fly-auto-singbox/config/fly.env.example`

**Steps:**
1. 增加平台/架构检测函数（linux/darwin + amd64/arm64）。
2. 增加 release 解析函数（latest 非 prerelease 或指定版本）。
3. 执行安装：下载 tarball -> 解压 -> install 到目标目录。
4. dry-run 仅打印命令，不执行下载。

### Task 3: 测试与文档

**Files:**
- Modify: `fly-auto-singbox/tests/test_pipeline.sh`
- Modify: `fly-auto-singbox/README.md`

**Steps:**
1. 在测试中用本地 `releases.json` 驱动 `--dry-run`，断言 URL/安装路径输出。
2. 更新 README 的安装章节与命令示例。
3. 运行测试与语法校验。
