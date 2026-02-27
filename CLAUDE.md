# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目目标

`fly-auto-singbox` 用 `./fly` 一套命令，将"订阅提取 + QX/Clash 规则转换 + sing-box 配置生成 + 运行管理"串成稳定流程，核心目标是兼容 sing-box VT `1.11.4`（桌面与 iOS 双端）。

## 常用命令

```bash
# 安装依赖
python3 -m pip install -r requirements.txt

# 初始化（从 config_template/ 生成 config/ 下的用户配置文件）
./fly init

# 主流水线（按顺序执行）
./fly extract                          # 从订阅提取节点 -> build/nodes.json
./fly build-rules                      # QX/Clash 规则转换 -> config/route-rules.json
./fly build-config                     # 生成桌面配置 -> config.json
./fly build-config --target ios        # 生成 iOS 配置 -> config.ios.json

# Ruleset 模式（生成远端引用的小体积配置）
./fly build-rules --ruleset --base-url "https://raw.githubusercontent.com/<user>/<repo>/main/ruleset"
./fly publish-ruleset                  # 提交 ruleset/*.srs 到 Git
./fly build-config --ruleset           # 生成引用 ruleset 的桌面配置
./fly build-config --target ios --ruleset  # iOS + ruleset

# 一步完成提取+构建
./fly pipeline
./fly pipeline --target ios --ruleset

# 运行管理
./fly on / ./fly off / ./fly status / ./fly log

# sing-box 安装
./fly check-singbox
./fly install-singbox --version 1.11.4

# 运行测试（唯一测试入口）
bash tests/test_pipeline.sh
```

## 代码架构

### 主入口

`fly`（Bash 脚本）负责：环境变量加载（`config/fly.env`）、命令路由、sing-box 启停、ruleset 发布（git add/commit/push）。所有 Python 脚本通过 `python3 scripts/*.py` 调用。

### 三段式核心流水线

```
订阅 URL
   └─> scripts/extract_nodes.py       -> build/nodes.json
          (过滤 US/HK/SG/JP，支持 SS/VMess/VLESS/Trojan/Hysteria2/TUIC 等)
                  |
        config/rule-sources.json
   └─> scripts/build_route_rules.py   -> config/route-rules.json
                                         config/route-rules.ruleset.json (--ruleset)
                                         ruleset/*.json + *.srs (--ruleset)
                  |
        config/base-template.json (桌面)
        config/base-template.ios.json (iOS)
        config/group-strategy.json
   └─> scripts/build_config.py        -> config.json / config.ios.json
```

### build_config.py 的注入逻辑

`build_config.py` 在模板基础上自动注入两类内容：

1. **Outbounds（来源分组 + 地区聚合 + 业务组 + Proxy 顶层）**：
   - 来源+地区组（如 `A-HongKong`）：HK/SG/JP 使用 `urltest`，America 使用 `selector`
   - 地区聚合组（如 `HongKong`）：`region_defaults` 控制默认值
   - 业务/自定义组（如 `Streaming`、`AI`）：来自 `group-strategy.json`
   - 顶层 `Proxy`

2. **连通性默认规则（route + dns）**：
   - `hijack-dns` 接管 DNS
   - QUIC reject（`protocol=quic` + `udp:443`）
   - `ip_is_private -> direct`
   - DNS 服务器注入（Bulianglin 风格：`default-dns`、`system-dns`、`block-dns`、`google`）
   - `dns.final = "google"`、`dns.strategy = "ipv4_only"`

### VT 1.11.4 兼容策略

`--target ios` 会触发：
- 清除 `dns.servers[].type` 字段（VT 1.11.4 不支持新格式，会崩溃）
- 清除 `route.default_domain_resolver`（同上）
- 只保留 `tun` inbound（不含 `mixed`）
- 更保守的 DNS / route 注入

桌面端同样使用 legacy DNS `address` 格式（无 `type` 字段），以兼容 VT 1.11.4。

### 关键约束

- **双端必须同时可用**：修改 DNS / route 逻辑时，桌面与 iOS 两端都必须通过 `bash tests/test_pipeline.sh`。
- **不使用旧版特殊出站**：`block` / `dns` 不能出现在 `route.rules[].outbound`，应用 `action: reject` / `action: hijack-dns`。
- **`direct` / `block` 不出现在最终 outbounds 列表**：由 `dns_direct` 等内部出站代替。
- **不使用 geosite/geoip 字段**：所有 GeoIP/GeoSite 走 `rule_set`（sing-box 1.8+ 迁移方向）。
- `example/` 目录下文件可能含敏感订阅信息，**禁止 git add / push**。

### 常见错误与排查

| 错误信息 | 原因 | 排查方向 |
|---|---|---|
| `dns.servers[0].type unknown field` | iOS/VT 1.11.4 收到新格式 DNS 配置 | 检查 `build_config.py` 的 iOS 分支是否正确清除了 `type` 字段 |
| `outbound detour not found: direct` | DNS 规则引用了不存在的 outbound | 检查 `dns.rules[].server` 引用的 outbound tag 是否存在 |
| ruleset 拉取 404 | `RULESET_BASE_URL` 配置错误或未 push | 检查 `fly.env` 里的 URL + 确认 `./fly publish-ruleset` 成功 |
| `no US/HK/SG/JP nodes found` | 节点名称不含地区关键词 | 检查订阅节点名称，参考 `build_config.py` 中的 `REGION_PATTERNS` |

## 配置文件说明

- `config/fly.env`：所有路径与运行参数的环境变量，优先在这里调整
- `config/base-template.json` / `config/base-template.ios.json`：sing-box 配置骨架（inbounds/dns/route 基础结构）
- `config/group-strategy.json`：分组结构（地区默认值、业务组、Proxy 成员）
- `config/route-rules.json`：分流规则（`build-rules` 生成，或手工编辑）
- `config_template/*.example*`：`./fly init` 的来源模板，不直接参与运行

## 外部参考资料

- sing-box 官方文档：`https://sing-box.sagernet.org/`
- Migration 总入口：`https://sing-box.sagernet.org/migration/`
- 本项目分析笔记：`docs/bulianglin-dns-leak-borrowing-notes.md`
- 未来工作事项：`docs/future-work.md`

> 查阅外部资料优先级：官方文档 > 本仓库分析文档 > 社区文章。版本基线为 VT `1.11.4`，1.12+ 新格式修改建议做版本开关而非直接替换。
