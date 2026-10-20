# AGENTS.md — VSC Library

First establish the checkout boundary. The standalone VSC Library checkout is
the only place to maintain shared files, whether selected directly or from the
parent Literature workspace. A consuming project's vsc-library
submodule is entirely read-only: no local notes, edits, deletes, refreshes,
formatting or generated files there. Its parent repository owns docs/VSC.md.

## Scope and sources

This is a project-neutral HPC knowledge base and template collection. Focus the
guides on KU Leuven / UHasselt wICE, Mindwell and KU Leuven Open OnDemand.
The generated snapshot also retains other VSC sites and historical material;
never mix their rules with current Leuven policy.

Read README.md, SOURCES.md, UPSTREAM_CHANGES.md and the relevant guide first.
Verify operational claims from the exact official source revision and use
the live status page for availability. Do not claim a resolved incident,
installed driver version, live quota, CUDA compatibility or job success
without current evidence. Prefer source paths and RST labels over dump lines.

## Maintenance

- Never edit VSC Repository.txt, sources.json or UPSTREAM_CHANGES.md by hand.
  Use scripts/refresh.py, then review affected guides and templates.
- Use scripts/review.py only after actually reviewing its changed source.
  Never clear review flags just to make checks pass.
- Preserve the official license and source provenance. Inventory binary
  sources; do not turn images or PDFs into fabricated plain text.
- Keep guides and references together in guides/. Keep Slurm examples flat
  under slurm templates/. Do not create empty folders or duplicate guides.
- Project-specific choices belong in the consuming project's docs/VSC.md.
  There is no exception for a PROJECT_SPECIFIC file inside this library.
- Templates must use Linux Bash with LF endings, an explicit cluster,
  partition, account placeholder, walltime and resource request. Quote paths.
  Do not depend on variable expansion in SBATCH directives or the script's
  spool-directory location. Modules/environment hooks belong to the consumer.
- Keep accounts, paths and examples neutral. Never copy credentials, personal
  VSC identifiers, private dataset names or real research-group storage IDs.
- Never submit cluster jobs, install into shared HPC environments, requeue
  research workloads or remove user results as part of library maintenance.
- Log substantive authored changes in CHANGELOG.md, newest date first.
  Run scripts/maintain.py --check-only and appropriate regression checks.
  Offline tests are not evidence that the examples ran on VSC.

## Git

The owner authorized initial creation/publication and the scheduled source-only
refresh. Subsequent manual commits and pushes require an explicit request.
Never commit or push a consuming project on the owner's behalf unless asked.
Never update a consumer to an unpublished local library commit.

Daily automation may update only generated source/provenance, its review
report, license and changelog after checks pass. It must not change guides,
templates, consumer pins or source-review acknowledgements automatically.
