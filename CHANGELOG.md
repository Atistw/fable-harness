# Changelog

All notable changes to Fable Harness are recorded here.

This kit follows [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`:

- **MAJOR** — a breaking change to the protocol contract (a hook/skill/agent removed or renamed, or an incompatible change to how the protocol is injected or how agents are dispatched) that would require users to re-install or change their setup.
- **MINOR** — a backward-compatible addition (a new hook, skill, agent, or governance rule) that existing installs keep working alongside.
- **PATCH** — a backward-compatible fix or wording change (a bug fix in a hook, a clarified rule, a typo).

The current version is also kept in [VERSION](VERSION).

## [Unreleased]

### Added

- **Protocol §1 — hard bounds (防空轉)**: the OODA loop now carries explicit retry ceilings — 3 consecutive failures of the same verification → stop and hand back to the user with the evidence and failure log collected so far (no unbounded rewrite-and-retry); 2 consecutive fruitless searches for the same information → stop searching and state what is missing and where it could be found. Hitting a ceiling and handing back is framed as correct behavior; concealed spinning is the failure. (Concept adapted from [Sahir619/fable-method](https://github.com/Sahir619/fable-method)'s hard bounds.)
- **Protocol §4 — non-code evidence sets**: Definition of Done now covers non-coding work with per-task-type evidence standards — research/fact-checking (named facts carry source links; primary sources preferred, secondary flagged), reports/summaries (every conclusion traceable to source material; unsupported inference labeled 推測), diagnosis/strategy calls (major conclusions must pass §2 adversarial review or be labeled 未抗辯假設), and batch data processing (before/after counts reconciled + sampled content checks; "all done" claims require count evidence).
- **`stop_gate.sh` heartbeat wrapper**: the Stop hook now goes through a shell wrapper that invokes Python (`py -3` version-independent launcher, `python3` fallback) and writes a `.last_stopgate` marker **after the gate returns successfully** — interpreter-level death (launcher gone, Python upgraded away) shows up as a stale marker against a fresh `.last_promptsubmit`.
- **`.gate_fail` post-mortem marker**: verify_gate's fail-open handler appends one line (timestamp + exception repr) to a gitignored `.gate_fail` file before swallowing, in a nested try so telemetry itself can't break fail-open. Test T13 (marker write) covers it; internal-failure tests run against a tmp copy of the gate so routine test runs never pollute the production marker. Suite is now 13 gate cases.
- **Maintainer guide** (`MAINTAINING.md`, + 繁體中文 translation): the PR merge SOP for keeping the contributor list clean — squash-merge and drop the `Co-Authored-By: Claude <noreply@…>` trailer so no phantom contributor appears.

### Changed

- **Docs**: the README "How it works" section (all five languages) now documents the token efficiency that falls out of the architecture — tiered model routing plus context-isolated, parallel sub-agents — noting that no Fable-specific benchmark figure is claimed.

### Fixed

- **verify_gate**: force UTF-8 stdout (`sys.stdout.reconfigure`) so the block JSON — whose reason string opens with "⛔" — survives Windows consoles that default to a legacy codepage (e.g. cp950). Without it the print raised `UnicodeEncodeError`, the fail-open wrapper swallowed it, and the Stop gate silently never blocked. Adds regression test T12 (fail-then-pass verified: cp950 stdout goes from empty output to a correct block JSON).

## [1.0.1] — 2026-07-07

### Fixed

- **verify_gate**: `TEST_CMD_RE` now recognizes script self-test entrypoints — a `--test` flag on any command (e.g. `python3 zh_convert_safe.py --test`) counts as a test run, so the Stop gate no longer falsely blocks a turn that ran one. Look-alike flags (`--test-pypi`, `--testing`, `--tests`) stay blocked via a `(\s|$)` anchor. Adds test T11 (allow + block cases, fail-then-pass verified). Reported by [@Jia-Hong-Peng](https://github.com/Jia-Hong-Peng) in [#1](https://github.com/Miguok/fable-harness/pull/1).

## [1.0.0] — 2026-07-07

First tagged release. The kit is feature-complete and globally deployed.

### Included

- **Behavior protocol** injected at session start (`.claude/hooks/fable_protocol.md` + `inject_protocol.sh`), codename `FABLE-PROTOCOL-V1-CANARY`.
- **Per-turn nudge** (`.claude/hooks/prompt_nudge.sh`) and **verification gate** (`.claude/hooks/verify_gate.py`) with native cross-scope de-duplication.
- **Adversarial review** skill (`.claude/skills/adversarial-review/`) and the three opposition agents (`skeptic`, `red-team`, `simplifier`).
- **Model routing** table (`CLAUDE.md`) and **harness detector** (`scripts/detect_harness.py`).
- **Governance docs**: `model_dispatch_rules.md`, `cognitive_rubrics.md`.
- **Docs**: `README.md` and translations (繁體中文 / 简体中文 / 日本語 / 한국어), `INSTALL.md`, MIT `LICENSE` (+ 繁體中文 translation).
