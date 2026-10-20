# Credits, failures and support

## Credits

Compute credit accounts are shared accounting balances associated with eligible
users/projects. The selected account is required when submitting a Leuven job.
Mindwell uses regular credit accounts now; an old pilot example is not a promise
of free production compute.

Useful commands:

    sam-balance
    sam-quote --help
    sam-statement --account=YOUR_ACCOUNT
    sam-list-usagerecords --account=YOUR_ACCOUNT --start=2026-10-01 --end=2026-10-31

Use the current sam-quote syntax to quote your actual proposed allocation.
The OnDemand dashboard provides the credit overview announced in October 2026.
Account permissions determine which other users' detailed transactions you can see.

Credits depend on allocated resources and runtime, including CPU resources
reserved by memory requirements. GPU jobs charge the GPU component as well.
A request that occupies a whole node's memory can be charged for the blocked
cores even when the process only uses one thread.

The reviewed GPU rates are shown below as a reference, in credits per
allocated GPU-minute. CPU charges can be additional; these are not full-job
quotes and they do not imply equal throughput or equal cost per experiment.

| GPU | Credits / GPU-minute |
|---|---:|
| P100 | 41.667 |
| V100 | 59.583 |
| A100 | 141.667 |
| H100 | 569.444 |
| B200 | 437.500 |

Check the current credit source and live billing configuration before making
a budget decision. A faster completed job can cost less overall even when
its nominal device rate is higher; measure the actual workload.

## Troubleshooting order

| Symptom | Check first |
|---|---|
| Cannot log in / nothing starts | Live service status and maintenance notices |
| Submission rejects partition | Explicit cluster, actual partition and requested resource limits |
| Account / balance warning | sam-balance, account membership, requested cost and quota |
| Long pending time | squeue reason, resource size, QoS, dependency and reservation |
| Python package missing | Exact interpreter, environment hook, module stack and kernel selection |
| CUDA unavailable / unsupported kernel | Actual allocated GPU, host driver, framework build and real operation preflight |
| GPU idle | CPU data preparation, worker counts, I/O, model placement and synchronization |
| GPFS path absent on P100/V100 | Pre-stage to Lustre; those nodes cannot access GPFS |
| No space / cannot write logs | Both byte and inode quota, HOME caches, DATA/project/scratch choice |
| Scratch files disappeared | Access-time purge and whether valuable inputs had persistent copies |
| Job killed / OUT_OF_MEMORY | State, exit code, host-memory peak, VRAM peak and worker duplication |
| TIMEOUT / interrupted writer | Latest complete checkpoint and manifest; preserve partial evidence |
| SQLite / shared-output conflicts | Actual concurrent writers, filesystem locking and one-writer ownership |

A slow GPU allocation is not automatically a driver bug. An import-only check
is not proof of model/kernel compatibility. A successful local test is not a
successful cluster run. Preserve the actual logs and completed artifacts.

## Support report

Use OnDemand's Help menu when available, or the service's published support
route. Include the cluster, job ID, time, partition, minimal resource request,
software versions, failing operation and relevant short error. State what
worked previously and whether a maintenance event overlaps the failure.
Remove access tokens, private keys, sensitive dataset contents and unrelated
personal/account information.

Check [live Leuven status](https://status.vscentrum.be/tier2_leuven.html) directly.
Incidents are time-sensitive and are not reclassified automatically by this
repository's source refresh.

Sources: source/leuven/credits.rst, source/leuven/slurm_accounting.rst,
source/leuven/slurm_specifics.rst and source/accounts/managing_disk_usage.rst.
