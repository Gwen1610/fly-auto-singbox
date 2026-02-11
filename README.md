# Auto sing-box with `fly`

`fly` 是一个配置驱动的一键脚本工具。  
你只需要填写订阅链接 + 节点分组 + 分流策略，然后执行 `fly apply`。

## 功能

- 一键初始化配置模板：`fly init`
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
SUBSCRIPTION_FORMAT="singbox"
SUBCONVERTER_URL=""
SINGBOX_VERSION="1.12.20"
INSTALL_DIR="/usr/local/bin"
CONFIG_PATH="/etc/sing-box/config.json"
SERVICE_NAME="sing-box"
INBOUND_LISTEN="127.0.0.1"
INBOUND_MIXED_PORT="7890"
LOG_LEVEL="info"
FINAL_OUTBOUND="proxy"
CHECK_URL="https://www.gstatic.com/generate_204"
```

说明：

- 如果 `SUBSCRIPTION_FORMAT=singbox`，`SUBSCRIPTION_URL` 需要直接返回包含 `outbounds` 的 sing-box JSON。
- 如果你的订阅不是 sing-box 格式，可设置：
  - `SUBSCRIPTION_FORMAT=clash` 或 `v2ray`
  - `SUBCONVERTER_URL=<你的 subconverter 接口地址>`

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
    "tag": "auto",
    "type": "urltest",
    "include_regex": "(hk|sg|jp|us)",
    "allow_empty": true,
    "url": "https://www.gstatic.com/generate_204",
    "interval": "5m",
    "tolerance": 50
  },
  {
    "tag": "proxy",
    "type": "selector",
    "members": ["auto", "all-proxies", "direct"]
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
      "domain_suffix": ["openai.com", "anthropic.com"],
      "outbound": "proxy"
    },
    {
      "geoip": ["cn"],
      "outbound": "direct"
    }
  ]
}
```

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
