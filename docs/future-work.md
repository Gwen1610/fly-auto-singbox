# Future Work

## Connectivity & Defaults

- Make QUIC blocking optional. Default keep `reject` for `protocol=quic` / `udp:443` for Safari stability, but allow re-enabling QUIC for selected domains when UDP is stable.
- Make “connectivity rule injection” optional. Provide a flag/env to disable injected `hijack-dns`, QUIC reject, private-ip direct, and DNS bootstrap rules for users who want a pure config.
- Improve bootstrap DNS rule precision. Replace the current “domain suffix guess” with Public Suffix List (PSL) based eTLD+1.
- Add IPv6 strategy knobs. Today we bias to stability (IPv4-first/IPv4-only style); add a user-facing option for dual-stack or prefer IPv6.

## urltest Tuning

- Expose `urltest` options (`interval`, `tolerance`, probe URL) via user config instead of hard-coded constants.
- Add per-region/per-provider overrides (some providers behave better with different probe URLs or intervals).

## Config Model & UX

- Move `URLTEST_REGIONS` into `config/group-strategy.json` so users can choose `selector` vs `urltest` per region without editing code.
- Add a “diagnostics mode” generator option to generate a config with extra logging and safe defaults for diagnosing DNS/QUIC issues.
