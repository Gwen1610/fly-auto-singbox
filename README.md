# Fly Auto Sing-box

## 1. 依赖

```bash
cd fly-auto-singbox
python3 -m pip install -r requirements.txt
```

## 2. 初始化

```bash
./fly init
```

会生成 5 个需要你编辑的文件：

- `config/fly.env`
- `config/extract.providers.json`
- `config/rule-sources.json`（由 `config_template/rule-sources.example.json` 生成）
- `config/group-strategy.json`（由 `config_template/group-strategy.example.json` 生成）
- `config/route-rules.json`（由 `config_template/route-rules.example.json` 生成）

## 3. 先检查是否已安装 sing-box

```bash
./fly check-singbox
```

- 如果输出 `not installed`，再执行安装。
- 如果输出已安装路径和版本，按需决定是否重装。

## 4. 自动安装 sing-box

默认安装（自动识别 Linux/macOS + 架构）：

```bash
./fly install-singbox
```

常用参数：

```bash
./fly install-singbox --version 1.11.4
./fly install-singbox --os linux --arch amd64
./fly install-singbox --install-dir /usr/local/bin
./fly install-singbox --dry-run
./fly install-singbox --force
```

安装逻辑：

- 默认先检查当前已安装版本。
- 目标版本已安装时会跳过下载。
- 用 `--force` 可强制重装。

安装后再次校验：

```bash
./fly check-singbox
which sing-box
sing-box version
```

## 5. 订阅链接填哪里

编辑 `config/extract.providers.json`，在 `subscribes[].url` 填你的订阅链接或本地订阅文件路径。

最小示例：

```json
{
  "subscribes": [
    {
      "tag": "default",
      "enabled": true,
      "url": "https://example.com/subscription",
      "prefix": "",
      "emoji": 0,
      "ex-node-name": ""
    }
  ]
}
```

提示：

- `subscribes[].enabled` 必须是 `true` 才会生效。
- `subscribes[].tag` 建议明确写（例如 `A`、`B`），用于后续自动生成 `A-HongKong`、`B-HongKong` 这类来源分组。
- `subscribes[].url` 是订阅链接时应为 `http/https`，程序会先下载再解析。
- 如果节点名称里没有地区标识（US/HK/SG/JP 或对应中文/常见缩写），提取会失败。

## 6. 提取节点（只提 US/HK/SG/JP，不加分流）

```bash
./fly extract
```

输出文件：

- `build/nodes.json`

常见报错：

- `no US/HK/SG/JP nodes found after filtering`
  - 先检查你的订阅节点名称是否包含地区关键词（例如 `US01`、`HK`、`SGP`、`JP`、`美国`、`香港`、`新加坡`、`日本`）。
  - 报错里会输出 sample tags，可据此判断命名是否可识别。

## 7. 从 QX/Clash 规则生成 route-rules.json（可选）

先编辑 `config/rule-sources.json`。

最小示例：

```json
{
  "final": "Proxy",
  "sources": [
    {
      "tag": "OpenAI",
      "enabled": true,
      "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/OpenAI/OpenAI.yaml",
      "outbound": "America"
    }
  ],
  "manual_rules": [
    "DOMAIN-SUFFIX, ai.dev, America",
    "HOST, aistudio.google.com, America",
    "DOMAIN-SUFFIX, moonshot.cn, Direct",
    "GEOIP, CN, Direct"
  ]
}
```

生成命令：

```bash
./fly build-rules
```

如果你希望在 iOS/VT 等客户端避免“内联大规则导致 config.json 过大/启动失败”，可以选择把 QX 规则**编译成 sing-box rule-set（.srs）并在配置里引用 URL**（生成一个更小的 ruleset 规则文件 `config/route-rules.ruleset.json`）：

```bash
# 1) 在 config/fly.env 里设置 RULESET_BASE_URL（指向你 GitHub 上 ruleset 目录的 raw 地址）
#    例：https://raw.githubusercontent.com/<user>/<repo>/main/ruleset
# 2) 生成 ruleset/*.srs + 小体积的 config/route-rules.ruleset.json
./fly build-rules --ruleset

# 3) 发布 ruleset/ 到 GitHub（只提交 ruleset/ 目录）
./fly publish-ruleset

# 4) 再生成最终配置：
#    - 电脑端：config.json
#    - iOS 端：config.ios.json
./fly build-config --ruleset
./fly build-config --target ios --ruleset
```

也可以不改 `fly.env`，直接传参：

```bash
./fly build-rules --ruleset --base-url "https://raw.githubusercontent.com/<user>/<repo>/main/ruleset"
```

说明：

- `build-rules --ruleset` 会为每个启用的 `sources[].url` 生成一个 `rule_set` 标签（默认前缀 `qx-`）。
- 当 `sources[].tag` 含中文/特殊字符导致无法生成稳定 slug 时，会自动回退为 `qx-source-<hash>`，避免文件名冲突且更稳定。
- `./fly build-ruleset` 仍可用，但只是 `./fly build-rules --ruleset` 的兼容别名。

另外，iOS sing-box VT（核心 `1.11.4`）下，“极简但不含 `dns` 配置”的 JSON 往往会直接启动失败并只提示 “internet error”，而不会产生日志；推荐从本仓库的 iOS 模板（带 `dns`）开始改，而不是从 ultra-min 配置开始删字段。

输出文件：

- `config/route-rules.json`
- `config/route-rules.ruleset.json`（ruleset 模式）

说明：

- 这是独立模块，只负责转换规则并生成 `route-rules.json`。
- 不会修改 `build/nodes.json` 和 `config.json`。
- 你也可以不使用它，继续手动编辑 `config/route-rules.json`。
- `manual_rules` 支持直接写 QX 风格单行规则（`类型, 值, 出口`）。
- 出口名支持别名：`Direct -> direct`、`Reject -> block`（会自动规范化）。
- `GEOIP,<CC>,Direct` 会自动转换为 `rule_set=geoip-<cc>`（兼容 sing-box 1.12+）。
- `build-rules` 的 `sources[]` 现在支持两种写法（二选一）：
  - `url`: 继续使用 `.list/.yaml/.txt` 规则源（会展开成 `domain/domain_suffix/...` 数组）
  - `rule_set`: 直接引用 sing-box 的规则集标签（更小、更快、对部分客户端更友好）
- 默认输出为带缩进的 JSON，便于人工阅读与维护。
- 如果你的客户端在导入/启动时对大 JSON 很慢或会崩溃，可以在生成时加 `--compact` 输出无缩进的紧凑 JSON：
  - `./fly build-rules --compact`
  - `./fly build-config --compact`

`rule_set` 示例（无需下载/展开大列表）：

```json
{
  "tag": "Ads",
  "enabled": true,
  "rule_set": ["category-ads-all"],
  "outbound": "Reject"
}
```

仓库内置了一个 `rule_set` 版本的参考模板：`config_template/rule-sources.ruleset.example.json`。

## 8. 注入分流规则生成最终配置

```bash
./fly build-config
```

如果你使用了 ruleset 规则（`./fly build-rules --ruleset`），则运行：

```bash
./fly build-config --ruleset
```

如果你想生成 iOS 端配置（更偏兼容 VT `1.11.4`），则运行：

```bash
./fly build-config --target ios
./fly build-config --target ios --ruleset
```

输入规则文件：

- `config/route-rules.json`（默认由 `config_template/route-rules.example.json` 生成）
- `config/route-rules.ruleset.json`（`build-rules --ruleset` 生成）
- `config/group-strategy.json`（默认由 `config_template/group-strategy.example.json` 生成）

默认内容：

- `final` 为 `Proxy`
- `rules` 为空数组（即不做任何分流规则，只走你在 `Proxy` 里选的出口）

你要加分流时，只改 `config/route-rules.json` 即可。

另外，`build-config` 会为“实际可用性”注入一些默认行为（无需你手改 `config.json`）：

- 为 `tun`/`mixed` 入站开启 `sniff` 与 `sniff_override_destination`（改善按域名/协议识别体验）。
- 在 `route.rules` 前置注入 `hijack-dns`（接管系统 DNS）、QUIC `reject`（`protocol=quic` / `udp:443`）、以及 `ip_is_private -> direct`。
- 在 `dns` 中注入 `local` 与 `google` 两个 server，并通过规则实现“节点域名 bootstrap 走 local”和“Google/YouTube 域名走 google”。

> 注：以上“默认注入”以 `--target desktop` 为准；`--target ios` 会使用更保守的注入策略（更贴近 VT `1.11.4` 的兼容性需求）。

输出文件：

- `config.json`
- `config.ios.json`（`--target ios`）

也可以一步跑完提取+构建：

```bash
./fly pipeline
```

如果你想一步生成 ruleset 规则 + ruleset 配置：

```bash
./fly pipeline --ruleset
```

如果你想一步生成 iOS 端配置：

```bash
./fly pipeline --target ios
./fly pipeline --target ios --ruleset
```

## 9. 分组设计哲学（分层选择器）

`build-config` 会按下面四层生成 outbounds 选择器：

1. 来源+地区层  
例如你有两个订阅 `A` 和 `B`，会生成 `A-HongKong`、`B-HongKong`、`A-America` 等组，每组只包含该来源该地区节点。

默认情况下：

- `HongKong`/`Singapore`/`Japan` 的来源+地区组使用 `urltest`（自动选最快）。
- `America` 的来源+地区组保持 `selector`（手动选择）。

2. 地区聚合层  
例如 `HongKong` 组会包含 `A-HongKong`、`B-HongKong`，默认值由 `group-strategy` 里的 `region_defaults` 决定（例如默认 `A-HongKong`）。

3. 业务分组层  
你可以在 `group-strategy` 的 `custom_groups` 自定义，例如 `Streaming`、`AI`，成员可引用地区组（如 `HongKong`、`America`）或其他已存在组。

4. 顶层 `Proxy`  
`Proxy` 的成员和默认值由 `group-strategy.proxy` 控制。你可以把 `Streaming`、`AI`、地区组混合放入。

示例（`config/group-strategy.json`）：

```json
{
  "region_defaults": {
    "HongKong": "A"
  },
  "custom_groups": [
    {
      "tag": "Streaming",
      "members": ["HongKong", "America"],
      "default": "HongKong"
    },
    {
      "tag": "AI",
      "members": ["HongKong", "America"],
      "default": "HongKong"
    }
  ],
  "proxy": {
    "members": ["Streaming", "AI", "HongKong", "America", "Singapore", "Japan"],
    "default": "HongKong"
  }
}
```

## 10. 启停与日志

启动：

```bash
./fly on
```

停止：

```bash
./fly off
```

状态：

```bash
./fly status
```

日志：

```bash
./fly log
```

关键运行文件：

- PID: `.sing-box.pid`
- Log: `sing-box.log`
- 终端颜色：
  - 交互终端里会用颜色区分信息（蓝=普通日志，黄=警告/未运行，红=错误，绿=成功状态）。
  - 非交互场景（管道、重定向、脚本捕获）自动关闭颜色，不影响解析。
  - 如需手动关闭颜色：`NO_COLOR=1 ./fly <command>`

## 11. 配置文件作用

- `config/base-template.json`
  - `build-config` 的主模板，定义 inbounds/dns/route 的基础骨架。
  - `build-config` 会在此基础上补齐 outbounds，并注入部分“连通性默认行为”（见上文第 8 节）。
- `config/base-template.ios.json`
  - iOS 端（VT `1.11.4`）更偏兼容的主模板（legacy DNS servers/address + 更保守的默认注入）。
  - 用法：`./fly build-config --target ios`（默认输出 `config.ios.json`）。
- `config_template/base-template.vt.legacy.example.json`
  - 旧写法（legacy DNS servers/address）的参考骨架，适合在某些客户端/旧核心下做兼容测试。
  - 用法：复制到 `config/` 后，在 `config/fly.env` 把 `BASE_TEMPLATE_FILE` 指向该文件再运行 `./fly build-config`。
- `config_template/rule-sources.example.json`
  - QX/Clash 规则源配置模板。
  - `./fly init` 会复制为 `config/rule-sources.json` 供你编辑。
  - `./fly build-rules` 读取这个文件生成 `config/route-rules.json`（默认 inline）。
  - `./fly build-rules --ruleset` 会生成 `config/route-rules.ruleset.json`（引用远程 `.srs`）。
- `config_template/rule-sources.ruleset.example.json`
  - `rule_set` 版本的规则源参考模板（不内联大列表）。
  - 适合 iOS/VT 客户端：建议配合 `./fly build-rules --ruleset` + GitHub raw URL 引用。
- `config_template/group-strategy.example.json`
  - 分层分组策略模板（来源组、地区组、业务组、Proxy 顶层）。
  - `./fly init` 会复制为 `config/group-strategy.json` 供你编辑。
  - `./fly build-config` 会读取这个文件来生成 selector 结构。
- `config_template/route-rules.example.json`
  - 分流规则参考模板。
  - `./fly init` 会复制为 `config/route-rules.json` 供你编辑。
  - 默认是空规则，不包含任何预置分流策略。

## 12. 实时交互命令（sing-box 运行中使用）

以下命令依赖 sing-box 的 Clash API，需要先 `./fly on` 启动 sing-box。

### 前置条件

`config/base-template.json` 中已内置 `experimental.clash_api`（默认监听 `127.0.0.1:9090`）。如需修改端口或启用密钥，同步修改 `config/base-template.json` 和 `config/fly.env` 中的 `API_HOST`/`API_SECRET`。

### 切换节点（不重启）

```bash
./fly select               # 列出所有 selector 分组，交互式切换
./fly select HongKong      # 直接进入 HongKong 分组的节点选择
```

交互风格与 Fish Tide `configure` 类似：按数字键选择，`q` 退出，`b` 返回上一级。

示例：

```
=== fly select — 选择分组 ===

  (1) Proxy                    [当前: HongKong]
  (2) HongKong                 [当前: A-HongKong] 12ms
  (3) America                  [当前: A-US-01]
  (4) Streaming                [当前: HongKong]

选择分组 [1/2/3/4/q]: 2

=== fly select — HongKong ===

  (1) A-HongKong               ★ 当前  12ms
  (2) B-HongKong               45ms
  (b) ← 返回分组列表

选择节点 [1/2/b/q]: 2
[fly] HongKong -> B-HongKong ✓
```

切换实时生效，新连接立即走新节点，无需重启。

### 测试延迟

```bash
./fly delay               # 对所有 selector 分组内节点测速
./fly delay HongKong      # 只测 HongKong 分组
```

输出按延迟排序，颜色编码：绿色 < 100ms，黄色 < 300ms，红色 ≥ 300ms 或超时。

### 实时监控面板

```bash
./fly monitor
```

进入实时刷新面板（3 秒自动刷新），展示：

- 运行状态 + 实时流量（↑ 上传 / ↓ 下载）
- 各 selector 分组当前选择 + 历史延迟
- 底部快捷键：`s` 切换节点，`d` 测延迟，`q` 退出

## 13. Future Work

见 `docs/future-work.md`。

## 14. 测试

```bash
bash tests/test_pipeline.sh
```

## 15. 署名

- 内置节点提取器代码来自开源项目 `sing-box-subscribe`。
- 原作者：`Toperlock`（仓库：`https://github.com/Toperlock/sing-box-subscribe`）。
- 规则转换模块参考了开源项目 `sing-box-geosite` 的映射思路。
- 原作者：`Toperlock`（仓库：`https://github.com/Toperlock/sing-box-geosite`）。
