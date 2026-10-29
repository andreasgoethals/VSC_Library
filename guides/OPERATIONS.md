# Credits, failures and support

## Credits

Compute credit accounts are shared accounting balances associated with eligible
users/projects. The selected account is required when submitting a Leuven job.
Mindwell uses regular credit accounts now; an old pilot example is not a promise
of free production compute.

KU Leuven users can request introduction credits (a limited amount of free
credits for test and development) and project credits for research and
production runs; see the Service Catalog. Introduction credits are held in a
personal account named intro_vscxxxxx, where vscxxxxx is your own VSC
username, and selected like any other account with --account. UHasselt users
use the credit request form; others contact their VSC coordinator.

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

### Cost formula

Each partition has Slurm TRESBillingWeights, inspectable with
scontrol show partitions --clusters=wice. Walltime is the number of minutes
the job actually ran:

    CPU-only job: CPU weight * effective cores * walltime
    GPU job:      (CPU weight * effective cores + GPU weight * GPUs) * walltime

So a GPU job pays the CPU rate for its cores in addition to the GPU rate.
The effective core count can exceed the request: a one-core job asking for a
full wICE node's memory blocks the node and counts as 72 cores.

Worked example from the source: two default-partition wICE Ice Lake nodes with
72 tasks each, running 2.5 hours (150 minutes):

    floor(2.546296296 * (2 * 72)) * 150 = 54 900 credits

sam-quote gives the same estimate when you prefix the submission command:

    $ sam-quote sbatch --account=YOUR_ACCOUNT --clusters=wice --nodes=2 \
                       --ntasks-per-node=72 --time=2:30:00 myjobscript.slurm
    54900

sam-quote assumes the worst case, in which the job runs until its time limit.

### Charge rates

Reviewed TRESBillingWeights, in credits per allocated CPU core or GPU per minute.
These are reference values from the reviewed source, not full-job quotes,
and they do not imply equal throughput or equal cost per experiment.

| Cluster | Resource | Type | Credits / minute |
|---|---|---|---:|
| wICE | Skylake | CPU core | 4.630 |
| wICE | Cascadelake | CPU core | 4.630 |
| wICE | Ice Lake | CPU core | 2.546 |
| wICE | Ice Lake (bigmem) | CPU core | 4.398 |
| wICE | Ice Lake (hugemem) | CPU core | 18.519 |
| wICE | Sapphire Rapids | CPU core | 3.472 |
| wICE | Zen4 Genoa | CPU core | 3.472 |
| wICE | P100 | GPU | 41.667 |
| wICE | V100 | GPU | 59.583 |
| wICE | A100 | GPU | 141.667 |
| wICE | H100 | GPU | 569.444 |
| Mindwell | Granite Rapids | CPU core | 2.604 |
| Mindwell | Granite Rapids (bigmem) | CPU core | 3.038 |
| Mindwell | B200 | GPU | 437.500 |

The CPU rates also apply to the cores of GPU jobs, per the formula above. For
example, the source's A100 partition configuration lists CPU=2.546296296
alongside the A100 GPU weight; check scontrol for the partition you use.
According to the wICE quick start, jobs on the wICE interactive partition do
not consume credits.

Check the current credit source and live billing configuration before making
a budget decision. A faster completed job can cost less overall even when
its nominal device rate is higher; measure the actual workload.

## Troubleshooting order

| Symptom | Check first |
|---|---|
| Cannot log in / nothing starts | Live service status and maintenance notices |
| Submission rejects partition | Explicit cluster, actual partition and requested resource limits |
| Account / balance warning | sam-balance, account membership, requested cost and quota |
| srun/mpirun CPU request mismatch | Explicit memory plus `--cpus-per-task`; inspect `SLURM_CPUS_PER_TASK` and `SLURM_TRES_PER_TASK`, then apply the [documented workaround](SLURM.md#explicit-memory-and-cpu-requests) |
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
source/leuven/slurm_specifics.rst, source/leuven/wice_quick_start.rst and
source/accounts/managing_disk_usage.rst.
