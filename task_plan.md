# Task Plan: fly 一键式 sing-box 自动化脚本实现

## Goal
Implement a foolproof `fly`-based automation toolkit that applies user config (subscription URL + node grouping + routing policy) and one-click deploys sing-box on Linux servers, with docs and GitHub-ready project structure.

## Current Phase
Phase 5

## Phases

### Phase 1: Implementation Scope Finalization
- [x] Confirm `fly` as execution entrypoint
- [x] Confirm configuration-driven workflow (subscription + groups + routing)
- [x] Lock initial command surface (`init/apply/status/logs/rollback`)
- **Status:** complete

### Phase 2: TDD Setup & Failing Tests
- [x] Add shell test harness for `fly`
- [x] Write failing tests for init and render behaviors
- [x] Run tests and confirm expected failures
- **Status:** complete

### Phase 3: Script Implementation
- [x] Implement `fly` command and subcommands
- [x] Implement config rendering and validation workflow
- [x] Implement backup/rollback and service operations
- **Status:** complete

### Phase 4: Documentation
- [x] Write Linux install/apply README
- [x] Document config schema and one-click flow
- [x] Add troubleshooting and rollback usage
- **Status:** complete

### Phase 5: GitHub Publishing
- [x] Initialize git repository (if absent)
- [ ] Commit project files
- [ ] Push to GitHub or provide precise publish handoff if auth/remote missing
- **Status:** in_progress

## Key Questions
1. Which sing-box features are most useful for fast server bootstrap and stable long-term operations?
2. How should `fly` keep user config simple while preserving extensibility?
3. What verification and safety checks are required so setup failures are visible and recoverable?

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| `fly` is the only user-facing runtime command | Matches user's explicit workflow preference |
| Use config-driven approach instead of manual CLI flags | Enables foolproof repeated deployments |
| Keep stable-by-default version policy (`1.12.x`) | Avoid pre-release compatibility breakage on production servers |
| Use embedded Python for JSON processing | Avoid hard dependency on jq in clean Linux environments |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `planning-with-files` skill name mismatch | 1 | Loaded using exact listed name `planning-with-files/skills/planning-with-files` |
| Missing path `/Users/dum/.codex/skills/planning-with-files/planning-with-files/SKILL.md` | 1 | Used available path `/Users/dum/.codex/skills/planning-with-files/skills/planning-with-files/SKILL.md` |

## Notes
- Re-read this file before final recommendations.
- Update phase status after each major milestone.
- Keep findings tied to source URLs and concrete dates/versions where possible.
