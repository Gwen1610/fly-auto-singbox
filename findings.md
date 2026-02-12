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

## 2026-02-12 (internal extractor extension)
- 已将订阅提取所需代码内置到仓库：`scripts/internal_subscribe/`。
- `scripts/extract_nodes.py` 已改为本地实现，不再 subprocess 调用外部 `sing-box-subscribe/main.py`。
- 默认流程现在仅依赖本仓库代码 + Python 依赖（`requests`、`PyYAML`）。
- 提取器新增无 `requests` 兼容路径：无该依赖时自动回退到 `urllib`。
- README 已补充必要信息：
  - 安装后校验命令（`which sing-box` / `sing-box version`）
  - 订阅填写位置（`config/extract.providers.json`）
  - 节点输出位置（`build/nodes.json`）
  - 最终配置输出位置（`config.json`）

## 2026-02-12 (install flow polish)
- 新增 `./fly check-singbox`：用于安装前检查本机是否已安装及当前版本。
- `install-singbox` 新增：
  - 已安装同版本时自动跳过下载；
  - `--force` 可强制重装；
  - `--dry-run` 会显示 `will_skip` 决策结果。
- README 增加开源来源署名：
  - 提取器来源项目：`Toperlock/sing-box-subscribe`
  - 原作者：`Toperlock`

## 2026-02-12 (extract compatibility fix)
- 发现线上报错 `no US/HK/SG/JP nodes found after filtering` 的主要原因是地区正则过严，无法覆盖 `US01/HK01/SGP/JP` 等常见命名。
- 已放宽 `extract` 和 `build-config` 的地区识别规则，并同步到 `internal_subscribe/tool.py`。
- `extract` 报错现在会返回 sample tags，方便定位节点命名是否可识别。
- 已新增 `config_template/minimal_four_regions.json` 兼容文件，避免旧路径引用报缺失。
- 进一步修复：从 `SHARE_PREFIXES` 移除 `http://` 和 `https://`，避免把订阅 URL 误判为节点 URI，导致不下载订阅内容。
- `extract.providers` 示例默认 `enabled` 调整为 `true`，降低初始化后踩坑概率。

## 2026-02-12 (route rules template + default no-split)
- 已将默认分流文件从仓库内固定 `config/route-rules.json` 调整为参考模板 `config/route-rules.example.json`。
- `./fly init` 现在会自动从 `route-rules.example.json` 生成可编辑的 `config/route-rules.json`。
- 默认路由策略改为不含分流规则：
  - `final = Proxy`
  - `rules = []`
- `tests/test_pipeline.sh` 已同步改为校验 `config.json` 中 `route.final=Proxy` 且 `route.rules` 为空。
- README 新增“配置文件作用”章节，明确：
  - `config/base-template.json`：运行时主模板；
  - `config_template/minimal_four_regions.json`：旧路径兼容模板；
  - `config/route-rules.example.json`：分流规则参考模板。
