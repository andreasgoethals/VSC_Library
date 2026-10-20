# Use the library in a research project

The standalone checkout owns shared VSC knowledge. A project's vsc-library
submodule is read-only. Its docs/VSC.md owns the application-specific answer:
what this project needs and how it runs.

## Add the submodule

Run from the consuming project's root:

    git submodule add -b main https://github.com/andreasgoethals/VSC_Library.git vsc-library
    git submodule update --init --recursive
    git submodule status -- vsc-library

Do not embed another Git repository using a normal folder copy. Do not edit
the submodule's contents or create a PROJECT_SPECIFIC file inside it.
Review and commit only the intended .gitmodules entry, submodule pin and
documentation. Do not include unrelated staged project work.

An existing clone receives registered submodules with:

    git submodule update --init --recursive

A fresh clone can use --recurse-submodules.
On VSC, fetch the updated parent repository and initialize its submodules
before following a guide introduced by that pin.

## What belongs in the parent's docs/VSC.md

Include:

- A link to vsc-library/README.md and the recorded library commit.
- The actual cluster, partition, account selection and resource measurements.
- Code, environment, input, cache, output and checkpoint locations, including
  the chosen Lustre/GPFS tier and group-storage protection policy.
- Exact setup, stage, preflight, submit, resume, monitor and result-transfer steps.
- Interpreter/toolchain/container identity and application-specific CUDA checks.
- Array identifiers, concurrency limits, output ownership and checkpoint contract.
- Links to project run logs and the source/configuration identity they validate.

Keep credentials and private keys outside tracked files. Project documentation
can refer to locally configured account/path variables without copying their
values into this shared public library.

For a file at docs/VSC.md, the library README link is ../vsc-library/README.md;
the snapshot link is ../vsc-library/VSC Repository.txt, with angle brackets
around its Markdown destination because the filename contains a space.

## Update a pin

    git submodule update --remote -- vsc-library
    git diff --submodule=log -- vsc-library
    git -C vsc-library rev-parse HEAD
    git add -- vsc-library

Read the library changelog and review flags. Update local docs/VSC.md only
where project instructions need to change. Commit the reviewed pin in the
parent. Updating this canonical library does not itself update a consuming pin.
Uncommitted TFM Library migration edits likewise do not reach old TFM pins.

## Daily update proposals

The shared library's GitHub Action automatically commits fresh official source.
For consuming projects, GitHub Dependabot supports Git submodules. Add this
entry to the parent's .github/dependabot.yml, preserving any existing entries:

    version: 2
    updates:
      - package-ecosystem: "gitsubmodule"
        directory: "/"
        schedule:
          interval: "daily"
          time: "07:23"
          timezone: "Europe/Brussels"
        allow:
          - dependency-name: "vsc-library"
        open-pull-requests-limit: 1
        commit-message:
          prefix: "docs"

Publish that file and the submodule registration on the parent's default branch.
Dependabot proposes a pull request when the pin can advance; you review and
merge it. Daily checks are subject to GitHub's schedule behavior. They do not
guarantee a new PR every calendar day or alter running jobs.

Automatic merging is a separate project policy and is not enabled by this
library. Leaving pin acceptance explicit preserves an experiment's reproducible
reference snapshot while eliminating manual discovery of updates.

The public VSC Library does not require a private-repository token for Dependabot.
If organization policy disables Dependabot or Actions, enable the appropriate
repository feature or keep using the manual commands above.

See [GitHub's Dependabot reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference).

## Maintenance in Codex

Open the parent `0. Literature` workspace, or the canonical `VSC Library` child,
as the local project for future shared-library work. Opening a README in another chat's panel
does not change that chat's recorded working directory.
Keep durable instructions in AGENTS.md and this README so the next chat can
continue from the files rather than reconstructing this conversation.
