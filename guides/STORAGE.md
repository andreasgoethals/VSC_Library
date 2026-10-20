# Storage, staging and transfer

## Choose storage by lifetime and I/O

| Variable / tier | Default Leuven quota | Intended role | Protection |
|---|---:|---|---|
| VSC_HOME | 3 GiB | Small configuration and personal files | Backup and snapshots |
| VSC_DATA | 75 GiB | Persistent modest-I/O files, code and compact logs | Backup and snapshots |
| VSC_SCRATCH | 500 GiB | Active compute working files | No backup; 30-day unused-file cleanup |
| VSC_SCRATCH_NODE | 200 GiB on P100/V100, 600 GiB on other listed Leuven nodes | Job-local temporary data | Removed when the job ends |
| Group project storage | Allocation-specific | Shared large persistent assets when approved | Verify that allocation's protection policy |

The HOME/DATA defaults apply to Leuven/Hasselt accounts; other home institutes
can have different quotas. Check both space and inode usage. A directory full
of small files can exhaust an inode quota before the byte quota.

Do not assume group project storage is backed up because personal DATA is.
Record the allocation's actual policy and restoration arrangements in the
consuming project's docs/VSC.md. Preserve valuable checkpoints and independent
copies of irreplaceable results.

## Lustre and GPFS are different compute tiers

wICE uses Lustre, while Mindwell uses IBM Storage Scale / GPFS. Intensive I/O
must use the filesystem native to the compute cluster. Cross-mounted storage
enables transfers, not a license to stream training data from the other cluster.
Administrators may cancel jobs that violate this rule.

VSC_SCRATCH resolves to the native scratch filesystem on the current node.
Use VSC_SCRATCH_LUSTRE1 and VSC_SCRATCH_GPFS1 when a transfer must name both
locations explicitly. VSC_PROJECT_LUSTRE1 and VSC_PROJECT_GPFS1 identify group
storage roots when available; the actual group directory is project-specific.

**GPFS is not accessible from the wICE P100/V100 nodes.** Stage their inputs
onto Lustre before submission and check every required path from the allocation.
Do not build a GPU job that depends on reading its environment from GPFS.

## Staging without losing work

1. Keep the authoritative inputs/checkpoints on approved persistent storage.
2. Stage the required working set to the native filesystem.
3. Verify sizes and, where useful, checksums before starting compute.
4. Give concurrent jobs separate temporary/cache locations; protect any shared
   result writer with a suitable lock or one-writer ownership.
5. Save durable results and checkpoints to their agreed permanent location.
6. Inspect the successful transfer before removing any source; these examples
   intentionally do not delete user data.

Scratch cleanup follows access-time policy. A move or timestamp-preserving
transfer can leave old timestamps on newly staged files. The official advice
for initial scratch copies is cp without -a. The transfer template likewise
does not preserve timestamps. Do not use periodic touching as a substitute
for moving inactive valuable data to appropriate storage.

Node-local scratch disappears after the allocation. Copying only during normal
exit is insufficient protection against a killed job or failed node; checkpoint
periodically to durable storage. Tar archives, SQLite databases and other
consolidated formats can reduce small-file load, but require a suitable
application format and concurrency contract.

## Transfers

Use login nodes only for transfers taking a few minutes. Longer Lustre/GPFS
copies belong in a transfer allocation, for example the
[transfer template](<../slurm templates/transfer.slurm>) on an interactive
partition where both filesystems are visible.

Globus is available for supported endpoints and large external transfers.
For Lustre–GPFS volumes exceeding 1 TB, Leuven specifically recommends transfer
jobs over Globus for performance. The best tool depends on the endpoints.
SCP/SFTP or the portal work for smaller transfers; do not assume a remote
environment variable expands on the local PowerShell side.

Compare manifests before replacing a populated dataset/cache. Never run a
recursive cleanup against a computed storage root without checking its exact
resolved path and ownership.

Sources: source/leuven/tier2_hardware/kuleuven_storage.rst,
source/leuven/tier2_hardware/parallel_filesystems.rst,
source/leuven/tier2_hardware/restoring_a_snapshot.rst,
source/accounts/managing_disk_usage.rst and source/data/storage.rst.
