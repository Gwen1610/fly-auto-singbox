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

会生成两个你要编辑的文件：

- `config/fly.env`
- `config/extract.providers.json`

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

- `config/route-rules.json`

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

## 9. 测试

```bash
bash tests/test_pipeline.sh
```

## 10. 署名

- 内置节点提取器代码来自开源项目 `sing-box-subscribe`。
- 原作者：`Toperlock`（仓库：`https://github.com/Toperlock/sing-box-subscribe`）。

## 11. 兼容文件

仓库内已提供：

- `config_template/minimal_four_regions.json`

用于兼容旧习惯/旧配置引用路径。
