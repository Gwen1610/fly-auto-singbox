# Fly

auto sing-box

在一台干净的 Linux 服务器上把 sing-box 跑起来，并提供本机代理端口（默认 `127.0.0.1:7890`）。
配置方式是三件事：订阅 + 节点分组 + 分流规则，其他交给 `./fly`。

## 适用场景

- 你只有“通用订阅链接”（base64/URI/Clash/v2ray 等），不想手工转格式
- 你想按地区分组（香港/美国/日本/韩国/新加坡），再按域名分流（默认：AI 走美国，Google 走香港）
- 你希望在服务器里用 `fly_on` / `fly_off` 快速给终端命令挂代理

## 环境要求

- Linux + systemd（脚本会创建 `/etc/systemd/system/<SERVICE_NAME>.service` 并管理它）
- 基础命令：`bash` `curl` `python3` `tar` `install`
- 可选：`docker`
  - 只有当你的订阅不是 sing-box JSON 时才需要转换
  - `SUBCONVERTER_URL` 指向本机且不可用时，`fly` 会尝试自动拉起本地 `subconverter` 容器
  - 默认允许自动安装 docker（为了把本机 converter 跑起来）；不想要的话看下面“如何关闭”部分

> `config/` `build/` `state/` 已写进 `.gitignore`，不会被提交。订阅链接仍然建议当成敏感信息保管。

## 快速开始

### 1) 下载

```bash
git clone https://github.com/Gwen1610/Auto_sing-box auto-sing-box
cd auto-sing-box
chmod +x fly
```

### 2) 初始化配置模板

```bash
./fly init
```

生成：

- `config/fly.env`
- `config/groups.json`
- `config/routes.json`

需要用“最新版默认模板”覆盖（会备份旧文件到 `state/*.bak.<timestamp>`）：

```bash
./fly init --force
```

### 3) 填订阅链接

编辑 `config/fly.env`，至少填一个：

- `SUBSCRIPTION_URL="..."`（常用）
- `SUBSCRIPTION_FILE="/path/to/subscription.json"`（本地已有 sing-box JSON 时）

最常用的配置通常就这几行：

```bash
SUBSCRIPTION_URL="https://example.com/sub"
SUBSCRIPTION_FORMAT="auto"
SUBCONVERTER_URL="http://127.0.0.1:25500/sub"
```

### 4) 先生成配置（不写入 /etc）

```bash
./fly apply --dry-run
```

会生成：`build/config.json`。

注意：`--dry-run` 会下载订阅并生成配置，但不会自动拉起本地 `subconverter`（不会调用 docker）。如果你的订阅需要转换，请先把 converter 跑起来，或把 `SUBCONVERTER_URL` 指向一个可用的 converter。

### 5) 正式部署（需要 root）

```bash
sudo ./fly apply
```

部署后默认开启本机代理端口：

- mixed inbound: `127.0.0.1:7890`（HTTP + SOCKS5 同端口）

### 6) 验证

```bash
./fly status
./fly logs -n 200
curl -I --max-time 15 --proxy socks5h://127.0.0.1:7890 https://www.gstatic.com/generate_204
```

## 配置说明

### config/fly.env

- `SUBSCRIPTION_FORMAT`
  - `auto`：自动识别（sing-box JSON / Clash / 通用 URI/base64）
  - `singbox`：订阅直接返回 sing-box JSON
  - `clash` / `v2ray`：强制走转换
- `SUBCONVERTER_URL`
  - 默认 `http://127.0.0.1:25500/sub`
  - 当订阅需要转换时会使用它
- `SUBCONVERTER_AUTO_START_LOCAL`
  - 默认 `true`
  - 当 `SUBCONVERTER_URL` 指向 `127.0.0.1/localhost` 且 converter 不可用时，是否允许 `fly` 自动拉起本机 `subconverter` 容器
- `SUBCONVERTER_AUTO_INSTALL_DOCKER`
  - 默认 `true`
  - 只在 `SUBCONVERTER_URL` 指向本机、且需要转换时才会用到
  - 设为 `false` 表示禁止 `fly` 自动安装 docker（建议你自己装，或用远端 converter）
- `SINGBOX_VERSION`
  - 默认 `1.12.20`
  - 也支持 `latest`（依赖 GitHub Releases API）

### config/groups.json（节点分组）

默认模板里已经包含：

- `hk-auto` / `hk-proxy`
- `us-auto` / `us-proxy`
- `jp-auto` / `jp-proxy`
- `kr-auto` / `kr-proxy`
- `sg-auto` / `sg-proxy`
- `proxy`（总入口）

分组两种写法：

- 正则匹配：`include_regex` / `exclude_regex`（支持英文缩写 + 中文地名）
- 手动列表：`members`

### config/routes.json（分流规则）

这是一个很薄的规则层：按 `domain_suffix` 命中后，把流量送到某个 `outbound`（比如 `hk-proxy` / `us-proxy`）。

默认模板：

- AI 相关域名 -> `us-proxy`（OpenAI / Claude / Gemini / Perplexity / Grok / Cursor / Copilot 等）
- Google / YouTube -> `hk-proxy`
- 其他 -> `final=proxy`

## 代理开关（给终端用）

`sudo ./fly apply` 会写入 `/etc/profile.d/fly-proxy.sh`，里面有三个函数：

- `fly_on`：设置 `ALL_PROXY` / `HTTP_PROXY` / `HTTPS_PROXY`
- `fly_off`：清空这些变量
- `fly_status`：查看当前状态

让当前 shell 立即可用：

```bash
source /etc/profile.d/fly-proxy.sh
fly_on
fly_status
```

说明：

- 环境变量只对“当前 shell 及其子进程”生效，不可能强行让整台机器所有进程立刻切换代理。
- 想让新开的 shell 默认可用，一般重连/重新登录即可（`/etc/profile.d` 会在登录时被加载；不同发行版/不同 shell 行为可能略有差异）。

手动等价写法（只想临时给当前 shell 用）：

```bash
export ALL_PROXY="socks5://127.0.0.1:7890"
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
```

## 常用命令

```bash
./fly init
./fly init --force

./fly apply --dry-run
sudo ./fly apply

./fly status
./fly logs -n 200
./fly logs -f -n 200

sudo ./fly rollback
sudo ./fly proxy-hooks-install
```

## 排障

- 订阅转换失败/`invalid subscription JSON`
  - 先看订阅原始内容：`curl -fsSL "$SUBSCRIPTION_URL" | head`
  - 如果是通用订阅，确认 `SUBCONVERTER_URL` 可用（本机容器或远端服务）
- `docker pull` 超时
  - 换镜像源或手动准备好 converter（把 `SUBCONVERTER_URL` 指向你能访问的 converter）
- 端口没起来
  - `./fly status`
  - `./fly logs -n 200`
  - `ss -lntp | grep 7890`

## 测试

```bash
bash tests/test_fly.sh
```

## 如何关闭“自动装 docker/自动起本机 converter”

编辑 `config/fly.env`：

- 禁止自动安装 docker：`SUBCONVERTER_AUTO_INSTALL_DOCKER="false"`
- 禁止自动拉起本机 converter：`SUBCONVERTER_AUTO_START_LOCAL="false"`

如果你两项都关了，又用了“通用订阅链接”，那就需要你自己把 converter 跑起来，或者把 `SUBCONVERTER_URL` 改成一个可用的远端 converter。
