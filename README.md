# VSC Library

Shared, offline-searchable HPC knowledge for projects using the Flemish
Supercomputer Centre, with practical guidance for KU Leuven / UHasselt,
wICE, Mindwell and KU Leuven Open OnDemand. This is a reference library,
not a Python package. Nothing needs to be installed into a research project.

The source of truth for site policy is the official documentation and live
service status. The guides explain it; the templates help apply it.

## Start here

1. Read [HPC basics and access](guides/HPC_AND_ACCESS.md).
2. Use [Open OnDemand](guides/ONDEMAND.md) for browser access.
3. Choose [hardware and resources](guides/CLUSTERS.md), then read
   [storage](guides/STORAGE.md) and [software](guides/SOFTWARE.md).
4. Adapt a [Slurm template](<slurm templates/README.md>) to your project.
5. Check [credits and troubleshooting](guides/OPERATIONS.md) before a costly run.

Check the [live Leuven status page](https://status.vscentrum.be/tier2_leuven.html)
before investigating a new access or scheduler failure.

## What is in this repository

| Path | Contents |
|---|---|
| [VSC Repository.txt](<VSC Repository.txt>) | Automatically scraped flat-text snapshot of the official VSC documentation repository |
| [sources.json](sources.json) | Exact upstream commit, source-file hashes, snapshot hash and excluded binary-asset inventory |
| [guides/](guides/) | Practical guides and source references together; no separate empty references folder |
| [slurm templates/](<slurm templates/>) | CPU, GPU, arrays, staging, checkpoint, interactive and multi-GPU examples, all one level deep |
| [UPSTREAM_CHANGES.md](UPSTREAM_CHANGES.md) | Which guides/templates need review after upstream source changes |
| [CHANGELOG.md](CHANGELOG.md) | Changes useful to consumers deciding whether to update |
| [SOURCES.md](SOURCES.md) | Provenance, scope, attribution and reference links |
| [scripts/](scripts/) | Source refresh, source-review recording and offline checks |
| [.github/workflows/](.github/workflows/) | Daily refresh and validation on GitHub |

There is no PROJECT_SPECIFIC file or template here. A consuming project's
own choices, paths, environment, credit account and run instructions belong
in that project's docs/VSC.md, outside the submodule.

## What “VSC Repository” means

The file is a scrape of
[hpcleuven/VscDocumentation](https://github.com/hpcleuven/VscDocumentation),
the source repository behind [docs.vscentrum.be](https://docs.vscentrum.be/).
It replaces the file formerly called VSC Documentation.txt in TFM Library.
It is generated, not a second independently maintained VSC manual.

All UTF-8 text in the upstream repository is included: generic HPC, accounts,
SSH/MFA, Slurm, software, data transfer, Leuven, other VSC sites and historical
pages. Their presence does not make every site's policy applicable to Leuven.
Search for FILE followed by the original source path. Cite that path or an RST
label rather than a dump line number.

Images, spreadsheets and PDFs are inventoried with hashes in sources.json and
remain available upstream. The existing PDFs concern old NX access and older
UGent Tier-1 presentations. There were no separate current Leuven reference
documents to justify another folder or duplicate downloads. New independently
useful references can be linked from the relevant guide.

## Refresh and validate

Python 3.10+ and Git are sufficient for refresh. Bash is also needed for shell
syntax checks; Git for Windows includes it. There are no pip dependencies.

    python scripts/maintain.py --check-only
    python scripts/maintain.py

The first command verifies the existing library and runs regression tests.
The second refreshes the official source first. Neither submits HPC jobs.
Run these only in the canonical checkout, never in a consuming submodule.

For a completed guide review:

    python scripts/review.py guides/STORAGE.md --note "Compared the changed storage policy with the guide and templates."
    python scripts/check.py --strict-review

Recording a review is an assertion that the changed source has actually been
read and the affected prose/templates checked. It does not write that prose.

## Daily automatic updates

The daily-source-refresh GitHub workflow checks the official master branch
daily at 04:17 UTC. It also supports Actions → Daily source refresh → Run
workflow. It retrieves one exact revision, regenerates the snapshot and
provenance, checks the result, runs tests, then commits only generated source
files, the source-change report, upstream license and changelog to this
repository's default branch. An unchanged revision creates no commit.

The source is downloaded and rendered before replacements begin. A failed
download, missing core document or unexpected reduction exceeding 50% refuses
the refresh. The previous files are restored if a later replacement fails.
No upstream program or setup script is executed.

**Automatic scraping does not automatically rewrite the curated guides.**
Each guide/template group records hashes of its reviewed source files.
Changes, deletions and new matching source pages produce visible review flags
in UPSTREAM_CHANGES.md. Normal integrity checks report these flags; strict
review checks fail until they are reviewed. This keeps the complete source
current without silently presenting older guidance as freshly verified.

GitHub runs this even when your computer is off. Scheduled runs can be delayed;
public-repository schedules can be disabled after 60 days without activity.
Use the Actions page to check failures or re-enable a disabled workflow.
See [GitHub's scheduling rules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## Use in another project

From the consuming repository's root:

    git submodule add -b main https://github.com/andreasgoethals/VSC_Library.git vsc-library
    git submodule update --init --recursive

Keep the mountpoint as vsc-library. Document that project's actual operating
instructions in docs/VSC.md; start with the checklist in
[consumer integration](guides/INTEGRATION.md).

Commit .gitmodules, the vsc-library pin and docs/VSC.md in that project when
you are ready to publish. A submodule is a pinned commit, so future library
updates do not change an experiment's reference material silently.

To receive the next published revision:

    git submodule update --remote -- vsc-library
    git diff --submodule=log -- vsc-library
    git add -- vsc-library

Review the change and commit the pin yourself. For a fresh clone:

    git clone --recurse-submodules PROJECT_REPOSITORY_URL

For automatic update proposals, use the daily Git-submodule Dependabot
configuration described in [consumer integration](guides/INTEGRATION.md).
It proposes pin updates; it does not merge them or change active cluster runs.

## Maintenance boundary

Edit shared material only in the standalone VSC Library checkout.
Downstream vsc-library folders are read-only, including for agent notes.
Keep user IDs, passwords, API keys, concrete group-storage IDs and project
credit accounts out of this public library. Templates use placeholders.
Preserve expensive outputs and checkpoints in consuming projects.

The upstream documentation's GPL-3.0 license is retained in [LICENSE](LICENSE).
See [SOURCES.md](SOURCES.md) for attribution.

## Shared Literature workspace

This independent repository can also live under the local `0. Literature`
workspace alongside other libraries. Its Git history and remote remain separate.
The shared entry points are `scripts/maintain.py` and
`scripts/propagate_to_downstream.py`; source-specific stages and identity are
defined in `scripts/library.json`. Both commands work in an independent clone.

From the parent workspace, `python scripts/maintain.py` runs libraries in
parallel. `python scripts/propagate_to_downstream.py --dry-run` previews updates
to existing consumer registrations under Projects; `--push` explicitly publishes
pin-only updates. Libraries are independent opt-ins, never an all-or-nothing bundle.
Pending registrations and unrelated consumer work must be preserved.
