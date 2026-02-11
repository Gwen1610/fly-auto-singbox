# Auto sing-box with `fly`

`fly` 是一个配置驱动的一键脚本工具。  
你只需要填写订阅链接 + 节点分组 + 分流策略，然后执行 `fly apply`。
默认支持“通用订阅链接”自动识别；需要转换时会优先使用本机 `subconverter`。

## 功能

- 一键初始化配置模板：`fly init`
- 强制重建默认模板（覆盖并备份旧文件）：`fly init --force`
- 按配置生成 sing-box 最终配置：`fly apply --dry-run`
- 自动部署到 Linux（安装 sing-box、写入配置、拉起 systemd 服务）：`sudo fly apply`
- 服务状态与日志：`fly status` / `fly logs`
- 失败回滚：`sudo fly rollback`

## 1. 在 Linux 服务器下载项目

### 方式 A：git clone

```bash
git clone <YOUR_GITHUB_REPO_URL> auto-sing-box
cd auto-sing-box
chmod +x fly
```

### 方式 B：下载压缩包

```bash
curl -L <YOUR_GITHUB_REPO_ARCHIVE_URL> -o auto-sing-box.tar.gz
tar -xzf auto-sing-box.tar.gz
cd auto-sing-box*
chmod +x fly
```

## 2. 初始化配置

```bash
./fly init
```

当你升级到新版本默认规则、想重建模板时：

```bash
./fly init --force
```

`--force` 会覆盖：
- `config/fly.env`
- `config/groups.json`
- `config/routes.json`

并在 `state/` 下自动备份旧文件（`.bak.<timestamp>`）。

会生成：

- `config/fly.env`
- `config/groups.json`
- `config/routes.json`

## 3. 填写你的配置

### 3.1 `config/fly.env`

至少填一个：

- `SUBSCRIPTION_URL`：机场订阅地址
- `SUBSCRIPTION_FILE`：本地 sing-box 订阅 JSON 文件路径

示例：

```bash
SUBSCRIPTION_URL="https://example.com/sub"
SUBSCRIPTION_FILE=""
SUBSCRIPTION_FORMAT="auto"
SUBCONVERTER_URL="http://127.0.0.1:25500/sub"
SUBCONVERTER_IMAGE="docker.1ms.run/tindy2013/subconverter:latest"
SINGBOX_VERSION="1.12.20"
INSTALL_DIR="/usr/local/bin"
CONFIG_PATH="/etc/sing-box/config.json"
SERVICE_NAME="sing-box"
INBOUND_LISTEN="127.0.0.1"
INBOUND_MIXED_PORT="7890"
LOG_LEVEL="info"
FINAL_OUTBOUND="proxy"
CHECK_URL="https://www.gstatic.com/generate_204"
ENABLE_DEPRECATED_SPECIAL_OUTBOUNDS="true"
```

说明：

- 推荐 `SUBSCRIPTION_FORMAT=auto`：会自动识别 `sing-box JSON` / `Clash` / `通用(base64 URI)` 订阅。
- 当检测到需要转换时，会使用 `SUBCONVERTER_URL`。如果它指向本机（默认 `127.0.0.1:25500/sub`）且不可用，`fly` 会尝试自动拉起本地 `subconverter` 容器。
- 你也可以手动指定：
  - `SUBSCRIPTION_FORMAT=singbox`（订阅直接返回 sing-box JSON）
  - `SUBSCRIPTION_FORMAT=clash` 或 `v2ray`（强制走转换）

### 3.2 `config/groups.json`（节点分组）

示例：

```json
[
  {
    "tag": "all-proxies",
    "type": "selector",
    "include_regex": ".*"
  },
  {
    "tag": "hk-auto",
    "type": "urltest",
    "include_regex": "((^|[^a-z])(hk|hong kong|hongkong)($|[^a-z])|香港|港线|港線)",
    "allow_empty": true,
    "url": "https://www.gstatic.com/generate_204",
    "interval": "5m",
    "tolerance": 50
  },
  {
    "tag": "hk-proxy",
    "type": "selector",
    "members": ["hk-auto", "all-proxies", "direct"]
  },
  {
    "tag": "us-auto",
    "type": "urltest",
    "include_regex": "((^|[^a-z])(us|usa|united states|america|la|los angeles|sjc|sfo|sea|ny|new york)($|[^a-z])|美国|美國|美西|美东|美東|洛杉矶|洛杉磯|纽约|紐約|西雅图|西雅圖|圣何塞|聖何塞|旧金山|舊金山)",
    "allow_empty": true,
    "url": "https://www.gstatic.com/generate_204",
    "interval": "5m",
    "tolerance": 50
  },
  {
    "tag": "us-proxy",
    "type": "selector",
    "members": ["us-auto", "all-proxies", "direct"]
  },
  {
    "tag": "jp-auto",
    "type": "urltest",
    "include_regex": "((^|[^a-z])(jp|japan|tokyo|osaka)($|[^a-z])|日本|东京|東京|大阪|日線|日线)",
    "allow_empty": true,
    "url": "https://www.gstatic.com/generate_204",
    "interval": "5m",
    "tolerance": 50
  },
  {
    "tag": "jp-proxy",
    "type": "selector",
    "members": ["jp-auto", "all-proxies", "direct"]
  },
  {
    "tag": "kr-auto",
    "type": "urltest",
    "include_regex": "((^|[^a-z])(kr|korea|south korea|seoul)($|[^a-z])|韩国|韓國|首尔|首爾|韩线|韓線)",
    "allow_empty": true,
    "url": "https://www.gstatic.com/generate_204",
    "interval": "5m",
    "tolerance": 50
  },
  {
    "tag": "kr-proxy",
    "type": "selector",
    "members": ["kr-auto", "all-proxies", "direct"]
  },
  {
    "tag": "sg-auto",
    "type": "urltest",
    "include_regex": "((^|[^a-z])(sg|singapore)($|[^a-z])|新加坡|獅城|狮城|新線|新线)",
    "allow_empty": true,
    "url": "https://www.gstatic.com/generate_204",
    "interval": "5m",
    "tolerance": 50
  },
  {
    "tag": "sg-proxy",
    "type": "selector",
    "members": ["sg-auto", "all-proxies", "direct"]
  },
  {
    "tag": "proxy",
    "type": "selector",
    "members": ["us-proxy", "hk-proxy", "jp-proxy", "kr-proxy", "sg-proxy", "all-proxies", "direct"]
  }
]
```

支持两种分组方式：

- 正则自动匹配节点：`include_regex` + `exclude_regex`
- 手动指定成员：`members`

### 3.3 `config/routes.json`（分流策略）

示例：

```json
{
  "final": "proxy",
  "rules": [
    {
      "domain_suffix": [
        "openai.com",
        "chatgpt.com",
        "oaistatic.com",
        "claude.ai",
        "anthropic.com",
        "gemini.google.com",
        "aistudio.google.com",
        "ai.google.dev",
        "generativelanguage.googleapis.com",
        "perplexity.ai",
        "perplexity.com",
        "x.ai",
        "grok.com",
        "cursor.com",
        "cursor.sh",
        "githubcopilot.com",
        "copilot.microsoft.com"
      ],
      "outbound": "us-proxy"
    },
    {
      "domain_suffix": [
        "google.com",
        "googleapis.com",
        "gstatic.com",
        "ggpht.com",
        "youtube.com",
        "googlevideo.com",
        "ytimg.com"
      ],
      "outbound": "hk-proxy"
    },
    {
      "geoip": ["cn"],
      "outbound": "direct"
    }
  ]
}
```

默认规则优先级说明：
- AI 域名先匹配，走 `us-proxy`（Gemini / Codex / Claude / Perplexity / Grok / Cursor / Copilot 等）。
- 通用 Google 域名后匹配，走 `hk-proxy`。
- 其余流量走 `final=proxy`，中国大陆 IP 走 `direct`。

## 4. 一键应用

先本地预览生成：

```bash
./fly apply --dry-run
```

正式部署（需要 root）：

```bash
sudo ./fly apply
```

## 5. 运行检查

```bash
./fly status
./fly logs -n 200
```

## 6. 回滚

如果新配置异常：

```bash
sudo ./fly rollback
```

## 7. 给 Codex/CLI 设置代理（示例）

部署成功后，如果你要让当前 shell 走本机代理：

```bash
export ALL_PROXY="socks5://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export HTTP_PROXY="http://127.0.0.1:7890"
```

## 8. 测试

项目自带最小测试：

```bash
bash tests/test_fly.sh
```

## 注意事项

- 本项目默认面向 `systemd` Linux 服务器。
- `fly apply` 会创建/覆盖 `/etc/systemd/system/<SERVICE_NAME>.service`。
- 首次部署建议先 `--dry-run`，确认配置生成无误后再正式应用。
