# Fly Auto Sing-box

全部代码都在本仓库内实现，不再依赖外部 `sing-box-subscribe` 目录。

## 1. 依赖

```bash
cd fly-auto-singbox
pip install -r requirements.txt
```

## 2. 初始化

```bash
./fly init
```

会生成三个你要编辑的文件：

- `config/fly.env`
- `config/extract.providers.json`
- `config/route-rules.json`（由 `config/route-rules.example.json` 生成）

## 3. 先检查是否已安装 sing-box

```bash
./fly check-singbox
```

- 如果输出 `not installed`，再执行安装。
- 如果输出已安装路径和版本，按需决定是否重装。

## 4. 自动安装 sing-box

默认安装（自动识别 Linux/mac + 架构）：

```bash
./fly install-singbox
```

常用参数：

```bash
./fly install-singbox --version 1.12.20
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

## 7. 注入分流规则生成最终配置

```bash
./fly build-config
```

输入规则文件：

- `config/route-rules.json`（默认由 `config/route-rules.example.json` 生成）

默认内容：

- `final` 为 `Proxy`
- `rules` 为空数组（即不做任何分流规则，只走你在 `Proxy` 里选的出口）

你要加分流时，只改 `config/route-rules.json` 即可。

输出文件：

- `config.json`

也可以一步跑完提取+构建：

```bash
./fly pipeline
```

## 8. 启停与日志

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

## 9. 配置文件作用

- `config/base-template.json`
  - `build-config` 的唯一主模板，定义 inbounds/dns/route 基础结构。
  - 运行时实际使用的是这个文件。
- `config/route-rules.example.json`
  - 分流规则参考模板。
  - `./fly init` 会复制为 `config/route-rules.json` 供你编辑。
  - 默认是空规则，不包含任何预置分流策略。

## 10. 测试

```bash
bash tests/test_pipeline.sh
```

## 11. 署名

- 内置节点提取器代码来自开源项目 `sing-box-subscribe`。
- 原作者：`Toperlock`（仓库：`https://github.com/Toperlock/sing-box-subscribe`）。
