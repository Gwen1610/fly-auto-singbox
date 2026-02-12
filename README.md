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

## 3. 自动安装 sing-box

默认安装：

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

安装后校验：

```bash
which sing-box
sing-box version
```

## 4. 订阅链接填哪里

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

## 5. 提取节点（只提 US/HK/SG/JP，不加分流）

```bash
./fly extract
```

输出文件：

- `build/nodes.json`

## 6. 注入分流规则生成最终配置

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

## 7. 启停与日志

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

## 8. 测试

```bash
bash tests/test_pipeline.sh
```
