# Changelog

## 2026-10-23

- Refreshed the official documentation snapshot to [1a0cf04a5aab](https://github.com/hpcleuven/VscDocumentation/commit/1a0cf04a5aab107021d98c563351f912a3caf062) (upstream commit date 2026-10-22); recomputed source hashes and guide review flags.

## 2026-10-20

- Fixed Slurm templates: per-worker thread limits in `multi_gpu.slurm` (previously 4 × 32 threads on 32 cores); `--open-mode=append` and a validated restart budget in `checkpoint.slurm`; `set -u` relaxed only while sourcing the project hook; `%j` log names for non-array jobs; caches on node-local scratch when available; retry-safe `transfer.slurm` (`--ignore-existing`, partial dir, explicit link handling) without preserving timestamps, per the scratch-cleanup policy.
- Guides: added the March 2026 firewall/certificate access rules, wICE bigmem/hugemem and the one-queued-`gpu_a100_debug` limit, intro credits, cost formulas, the full credit-rate table and a `sam-quote` example, `myquota`, and Apptainer, Miniforge3 and `vsc-venv` basics, each verified against the snapshot.
- Scripts read text explicitly as UTF-8; refresh changelog sections are dated by the refresh day (upstream commit date recorded inside) and inserted newest-first. Ten new regression tests.
- Shared entry points updated identically with DM/TFM: propagation rolls back a failed consumer pin commit; post-refresh rechecks run once with all flags.

- Joined the local Literature workspace while retaining an independent GitHub repository. Standardized configurable maintenance and exact-published-commit propagation; added consumer registration and unrelated-commit safeguards. Canonical edits are allowed from the parent workspace; downstream shared files remain read-only.

- Refreshed the official documentation snapshot to [9475d631a158](https://github.com/hpcleuven/VscDocumentation/commit/9475d631a15849b70d84642b17c226b1b89fd28d); recomputed source hashes and guide review flags.

- Created the independent VSC Library and migrated the shared VSC documentation out of TFM Library.
- Added combined guides/reference material, flat Slurm templates, exact upstream provenance and source-review tracking.
- Added daily GitHub source refresh and offline integrity, privacy, documentation and shell checks.
- Established consuming-project docs/VSC.md as the only place for project-specific VSC instructions.
- Checked checkpoint/requeue behavior and transfer path guards with isolated shell regressions; transfers refuse root and recursive destinations.
