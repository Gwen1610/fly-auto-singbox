# Claude Code 接手文档（2026-02-27 快照）

## 1. 项目目标（一句话）

`fly-auto-singbox` 的目标是：用 `./fly` 一套命令，把“订阅提取 + QX/Clash 规则转换 + sing-box 配置生成 + 运行管理”串成稳定流程，重点兼容 sing-box VT `1.11.4`（桌面与 iOS）。

---

## 2. 当前状态（接手前先看）

- 当前分支：`main`
- 当前基线提交：`1342e80`（`feat: extend Bulianglin CN DNS and route linkage`）
- 最近核心演进：
  - `8de7388`：默认生成 VT `1.11.4` 可用配置
  - `5c0e3da`：切到 Bulianglin 风格 DNS 模式
  - `1342e80`：补充 CN DNS / route 联动
- 已通过的关键验证（此前会话）：
  - `bash tests/test_pipeline.sh`
  - `./fly build-config`
  - `./fly build-config --target ios`

---

## 3. 工作目录索引（高优先级文件）

### 3.1 CLI 入口

- `fly`：主入口（命令编排、环境变量加载、启动/停止、ruleset 发布、构建流程）

### 3.2 核心脚本

- `scripts/extract_nodes.py`
  - 订阅读取与节点提取（只提 US/HK/SG/JP）
  - 输出：`build/nodes.json`
- `scripts/build_route_rules.py`
  - QX/Clash 规则转换
  - 支持两种模式：
    1) 内联规则输出 `config/route-rules.json`
    2) ruleset 输出 `config/route-rules.ruleset.json` + `ruleset/*.srs`
- `scripts/build_config.py`
  - 把节点与路由规则注入模板
  - 生成：
    - 桌面：`config.json`
    - iOS：`config.ios.json`
  - 内含 VT 1.11.4 兼容分支（DNS / route 注入差异）

### 3.3 运行时配置（本地可编辑）

- `config/fly.env`
- `config/extract.providers.json`
- `config/rule-sources.json`
- `config/group-strategy.json`
- `config/route-rules.json` / `config/route-rules.ruleset.json`
- `config/base-template.json`（桌面模板）
- `config/base-template.ios.json`（iOS 模板）

### 3.4 模板目录（初始化来源）

- `config_template/*.example*`
  - `./fly init` 会从这里生成 `config/*.json` 运行时文件

### 3.5 文档目录

- `README.md`：用户主说明（命令与配置使用）
- `docs/future-work.md`：后续可优化点
- `docs/bulianglin-dns-leak-borrowing-notes.md`：Bulianglin DNS 逻辑借鉴分析
- `docs/plans/*.md`：历史设计方案与阶段说明
- `task_plan.md` / `findings.md` / `progress.md`：长期工作轨迹

### 3.6 测试

- `tests/test_pipeline.sh`：当前唯一主测试，覆盖初始化/提取/规则转换/构建主链路

---

## 4. 当前能力边界（必须知道）

1. 默认目标核心是 VT `1.11.4`，不是 sing-box 最新迁移格式。  
2. `--target desktop` 与 `--target ios` 都需要保持可运行，不允许只修一端。  
3. QX 规则链路仍保留，且支持 ruleset 模式（`--ruleset`）来降低配置体积。  
4. `example/` 下有用户本地示例文件，仅作参考，不应进入公开仓库。  

---

## 5. 快速上手（Claude Code 建议执行顺序）

1. `git status --short` 先看工作区是否干净。  
2. `./fly help` 熟悉命令面。  
3. 先跑最小验证：
   - `bash tests/test_pipeline.sh`
4. 再按目标端单独构建：
   - `./fly build-config`
   - `./fly build-config --target ios`
5. 如涉及 ruleset 流程，再补：
   - `./fly build-rules --ruleset`
   - `./fly build-config --ruleset`

---

## 6. 已知风险与排查抓手

- 若出现 `dns.servers[0].type unknown field "type"`，通常是 iOS/VT 1.11.4 兼容格式被写成了新格式。  
- 若出现 `outbound detour not found: direct`，通常是 DNS 规则指向了不存在的 outbound tag。  
- 若 ruleset 拉取 404，优先检查：
  - `RULESET_BASE_URL` 是否正确
  - `./fly publish-ruleset` 是否实际 push 成功
  - 仓库分支与路径是否为 `main/ruleset/*.srs`

---

## 7. 接手建议（下一阶段）

- 保持“能运行优先”：先保证 `./fly build-config` 产物可直接导入并启动，再考虑结构优化。  
- 对 DNS / route 修改时，桌面与 iOS 逻辑必须同时审阅，避免一端修复另一端回归。  
- 若要迁移到 sing-box `1.12+` / `1.13+` 新格式，建议做“版本开关”而不是直接替换当前 VT `1.11.4` 分支。  
