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

## 2026-02-12 (remove legacy geosite/geoip strategy)
- 用户要求彻底移除历史预置分流策略（包括 `geosite-category-ads-all`、`geoip-cn` 等）。
- 已从 `config/base-template.json` 删除所有 `route.rule_set` 与 DNS 中 `rule_set` 相关内容。
- 现在默认模板只保留基础网络结构，不内置任何基于 geosite/geoip 的策略。
- `config_template/minimal_four_regions.json` 已删除，模板来源统一为 `config/base-template.json`。
- 测试新增断言：生成的 `config.json` 不应包含 `geosite` 或 `geoip` 字样。

## 2026-02-12 (terminal colors + markdown cleanup)
- `fly` 增加终端彩色输出：
  - 蓝色：普通 `[fly]` 日志；
  - 黄色：`warn`、`not running`、`already running`；
  - 红色：`die` 错误；
  - 绿色：`started/stopped/running`。
- 彩色输出仅在交互终端启用；当输出被重定向/管道时自动降级为纯文本，不影响脚本与测试解析。
- 支持通过 `NO_COLOR=1` 手动关闭颜色。
- markdown 收尾：为 `docs/plans/*` 增加 archive note，提示以 `README.md` 为当前行为准。

## 2026-02-12 (integrate sing-box-geosite style rule conversion)
- 新增独立命令 `./fly build-rules`，专门把 QX/Clash 规则源转换为 `config/route-rules.json`。
- 新增配置模板 `config/rule-sources.example.json`，`./fly init` 会自动生成可编辑的 `config/rule-sources.json`。
- 新增脚本 `scripts/build_route_rules.py`：
  - 支持 `.list/.yaml/.txt`；
  - 支持常见规则映射：`DOMAIN-SUFFIX/DOMAIN/DOMAIN-KEYWORD/IP-CIDR/...` 到 sing-box 对应字段；
  - 输出格式为 `{final, rules}`，直接被 `build-config` 消费。
- 转换模块保持解耦：仅生成 `route-rules.json`，不触碰节点提取或运行态命令。
- 兼容性修复：
  - 无 `requests` 时自动回退到 `urllib`；
  - 无 `PyYAML` 时使用最小 `payload` 解析回退；
  - 相对路径规则源支持 `sources 文件目录` 与 `当前工作目录` 双路径解析。

## 2026-02-12 (manual supplements + outbound alias normalization)
- 新增 `manual_rules` 字段：可直接在 `config/rule-sources*.json` 写 QX 单行规则（例如 `DOMAIN-SUFFIX, ai.dev, America`）。
- `build_route_rules.py` 现在会解析 `manual_rules` 并合并到输出 `route-rules.json`。
- 出口别名自动规范化：
  - `Direct -> direct`
  - `Reject -> block`
- `build_config.py` 已增加 `block` outbound，并在校验阶段对 `final/outbound` 做同样的别名规范化。
- 你的补充规则模式（`DOMAIN-SUFFIX/HOST/HOST-KEYWORD/GEOIP`）均已覆盖并通过测试。
