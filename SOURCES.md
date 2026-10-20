# Sources and provenance

## Primary offline source

[hpcleuven/VscDocumentation](https://github.com/hpcleuven/VscDocumentation)
is the official source repository behind
[VSC documentation](https://docs.vscentrum.be/). The tracked master branch is
scraped into [VSC Repository.txt](<VSC Repository.txt>). The exact commit,
commit date and per-file SHA-256 hashes are in [sources.json](sources.json).
The upstream [GPL-3.0 license](LICENSE) is preserved verbatim.

The scrape retains all text, including documentation-build configuration,
source code examples, other sites and old hardware pages. Binary assets are
listed in the manifest with their source path, size and hash; use the official
repository at the recorded commit to retrieve one. Nothing is installed or run
from the source repository.

The five existing PDFs are two legacy NX guides and three UGent Tier-1
presentations from 2021–2023. Spreadsheets are mostly old node maps, with a
wICE map as well. These do not form a separate current Leuven reference corpus.
The guides link authoritative references where they are useful.

## Current operational sources

| Topic | Official reference |
|---|---|
| VSC starting point | [Documentation](https://docs.vscentrum.be/) |
| wICE | [Quick start](https://docs.vscentrum.be/leuven/wice_quick_start.html) |
| Mindwell | [Quick start](https://docs.vscentrum.be/leuven/mindwell_quick_start.html) |
| Leuven scheduler policy | [Site-specific Slurm](https://docs.vscentrum.be/leuven/slurm_specifics.html) |
| Hardware | [Leuven Tier-2 hardware](https://docs.vscentrum.be/leuven/tier2_hardware.html) |
| Storage | [Leuven storage](https://docs.vscentrum.be/leuven/tier2_hardware/kuleuven_storage.html) |
| File-system selection | [Parallel filesystems](https://docs.vscentrum.be/leuven/tier2_hardware/parallel_filesystems.html) |
| Browser access | [Web portal documentation](https://docs.vscentrum.be/compute/portal/index.html) |
| Leuven browser service | [KU Leuven OnDemand](https://ondemand.hpc.kuleuven.be/) |
| Service incidents | [Leuven live status](https://status.vscentrum.be/tier2_leuven.html) |
| Scheduler command semantics | [Slurm manuals](https://slurm.schedmd.com/documentation.html) |

Service status is deliberately not a permanent availability claim in the guides.
The status page observed on 20 October 2026 reported urgent Tier-2 maintenance
starting 19 October, with login access closed and new jobs held. Consult the
live page for its subsequent state.

The explanation of the 1 October 2026 OnDemand release also uses the banner
quoted by the owner in this chat: credit dashboard, Help-menu support tickets,
Module Browser, removal of Genius, driver refresh and the P100/V100 migration.
This private-portal notice is identified as owner-provided evidence; the public
repository scrape does not claim to contain every authenticated portal notice.

## Project-derived patterns

The initial template design inspected the local research projects TabPFNCredit,
CreditPFN, CreditICL and JEVPFN, the generic project template, the older
TabPFNCredit-APA25 scripts and Readiness-To-Train. The last project had no Slurm
job scripts in the inspected checkout.

Reusable lessons include explicit cluster selection, choosing native Lustre
or GPFS storage, arrays with concurrency limits, explicit interpreter selection,
bounded numerical-library threads, cache placement outside HOME, application
preflight, resumable outputs, signals and transfer-before-compute workflows.
Project scripts are examples of usage, not authorities on current site policy.
They can retain historical Genius paths or outdated backup assumptions.
No project-specific account, group directory, dataset or checkpoint is copied here.

## GitHub automation references

- [Scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Dependabot configuration](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)

The GitHub actions used by the workflows are pinned to official action revisions.
