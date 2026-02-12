# Fly (Decoupled Pipeline)

这个版本把能力拆成 3 个独立模块：

1. `install-singbox`：自动下载并安装 Linux/mac 对应的 sing-box。
2. `extract` + `build-config`：先提取节点，再注入分流规则。
3. `on/off/status/log`：只负责 sing-box 后台进程生命周期管理。

`sing-box-subscribe` 作为外部依赖，不在本仓库修改。

## 命令

```bash
./fly init [--force]
./fly install-singbox [--dry-run]
./fly install-guide
./fly extract
./fly build-config
./fly pipeline
./fly on
./fly off
./fly status
./fly log
```

## 目录

- `fly`: 主命令入口
- `scripts/extract_nodes.py`: 节点提取模块（无分流）
- `scripts/build_config.py`: 分流注入模块
- `config/fly.env.example`: 运行配置模板
- `config/extract.providers.example.json`: 提取配置模板
- `config/route-rules.json`: 分流规则
- `config/base-template.json`: 基础 sing-box 模板

## 第一步：初始化

```bash
./fly init
```

会生成本地文件（可改）：

- `config/fly.env`
- `config/extract.providers.json`

## 第二步：自动安装 sing-box

```bash
./fly install-singbox
```

常用参数：

```bash
./fly install-singbox --version 1.12.20
./fly install-singbox --os linux --arch amd64
./fly install-singbox --install-dir /usr/local/bin
./fly install-singbox --dry-run
```

说明：

- 自动识别当前系统 `linux/darwin` 和 `amd64/arm64`。
- 从 GitHub Releases 自动匹配对应资产并安装。
- `install-guide` 现在是 `install-singbox --dry-run` 的兼容别名。

## 第三步：配置提取参数

编辑 `config/extract.providers.json`，填入你的订阅信息（与 `sing-box-subscribe` 兼容）。

编辑 `config/fly.env`，确认：

- `SUBSCRIBE_DIR` 指向你的 `sing-box-subscribe` 目录
- `SING_BOX_BIN` 指向本机 `sing-box` 可执行文件

## 第四步：生成配置（解耦两段）

只提取节点（无分流）：

```bash
./fly extract
```

会输出 `build/nodes.json`。

注入分流生成最终配置：

```bash
./fly build-config
```

会输出 `config.json`。

一键执行两段：

```bash
./fly pipeline
```

## 第五步：后台进程管理

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

说明：

- 默认使用 `sudo` 启停（适配 TUN 场景）。
- 进程管理基于 `nohup + .sing-box.pid`。
- 命令幂等：重复 `on/off` 不会产生脏状态。

## 测试

```bash
bash tests/test_pipeline.sh
```
