# 后续计划

这份仓库目前更偏“能直接用”的默认值。后续如果要做得更可控、可调，优先级大概是下面这些。

## 连通性与默认值

- 把 QUIC 屏蔽做成可选项：默认仍保持 `protocol=quic` / `udp:443` 的 `reject`（偏 Safari 稳定），但允许按域名放开。
- 把“连通性注入”（`hijack-dns`、QUIC `reject`、私网直连、DNS bootstrap）做成可选开关，方便生成更“纯净”的配置。
- DNS bootstrap 精度：用 Public Suffix List（PSL）做 eTLD+1 识别，替代简单的 domain suffix 猜测。
- IPv6 策略：增加双栈 / prefer IPv6 / IPv4-only 等用户可选项。

## urltest 调参

- 把 `urltest` 的 `interval` / `tolerance` / probe URL 暴露到用户配置，不要写死在代码里。
- 允许按地区/订阅源覆盖 urltest 参数（有些机场对不同 probe URL 的表现差异很明显）。

## 配置模型与可用性

- 把 “哪些地区用 urltest” 的策略下沉到 `config/group-strategy.json`，避免需要改代码。
- 增加一个“诊断模式”：生成更保守的路由与更详细的日志，专门用来排查 DNS/QUIC/规则集加载问题。
