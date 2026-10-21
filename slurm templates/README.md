# Slurm templates

All examples and the shared environment helper live directly in this folder.
They are starting points; offline syntax checks do not validate an application
or reserve any resources.

## Submission contract

Mount this library at vsc-library and submit from the parent project's root.
For Python jobs, the first two script arguments are:

1. Absolute project checkout directory.
2. Absolute Python executable from the intended environment.

All remaining arguments go to Python, except checkpoint.slurm, which first
consumes an explicit maximum automatic restart count.
The application can be a script or a module selected with -m.
Override REPLACE_ME with your authorized account at submission.
Adapt memory, CPUs, GPUs and time to a measured workload.

    sbatch --account=YOUR_ACCOUNT "vsc-library/slurm templates/cpu.slurm" "$PWD" /absolute/path/to/python -m your_package.prepare
    sbatch --account=YOUR_ACCOUNT "vsc-library/slurm templates/gpu_debug.slurm" "$PWD" /absolute/path/to/python -m your_package.gpu_preflight

The explicit interpreter avoids accidentally using another activated
environment. If that environment needs module loading or activation, put it in
the parent's scripts/vsc_environment.sh; the helper sources it before launch,
with nounset relaxed only while the hook runs. Stage model weights and datasets
before submitting. The helper's per-job caches start empty and are disposable.
They go to node-local VSC_SCRATCH_NODE when it is available, which is removed
when the job ends. Otherwise they fall back to VSC_SCRATCH/vsc-library-cache,
where finished jobs' cache directories remain until you remove them or the
scratch cleanup does; the log prints the cache path.

Logs are named slurm-JOBNAME-JOBID; the array template uses
slurm-JOBNAME-ARRAYJOBID_TASKID.

## Available files

| File | Purpose |
|---|---|
| [cpu.slurm](cpu.slurm) | Threaded CPU work on wICE |
| [cpu_mindwell.slurm](cpu_mindwell.slurm) | CPU work on Mindwell |
| [gpu_p100.slurm](gpu_p100.slurm) | Single P100 on wICE; Lustre-only inputs/environment |
| [gpu_v100.slurm](gpu_v100.slurm) | Single V100 on wICE; Lustre-only inputs/environment |
| [gpu_a100.slurm](gpu_a100.slurm) | Single A100 on wICE |
| [gpu_h100.slurm](gpu_h100.slurm) | Single H100 on wICE |
| [gpu_b200.slurm](gpu_b200.slurm) | Single B200 on Mindwell; native GPFS I/O |
| [gpu_debug.slurm](gpu_debug.slurm) | Short full-A100 debugging allocation |
| [array.slurm](array.slurm) | Ten independent CPU tasks, at most two active together |
| [multi_gpu.slurm](multi_gpu.slurm) | Four A100s on one node via torchrun; CPU threads divided per worker; application must implement DDP |
| [checkpoint.slurm](checkpoint.slurm) | Forward USR1 to a checkpoint-aware Python application; bounded opt-in requeue; appended logs |
| [transfer.slurm](transfer.slurm) | Retry-safe directory copy without deletion or overwriting in an interactive-partition allocation |
| [interactive.sh](interactive.sh) | Request an interactive login shell allocation |
| [environment.sh](environment.sh) | Quoting, interpreter check, thread bounds, temporary caches and run identity |

Array applications read SLURM_ARRAY_TASK_ID to select work and unique output
locations. The script does not silently append an application-specific flag.
Customize the array range and concurrency limit when submitting.

The transfer script takes two absolute directories instead of Python arguments:

    sbatch --account=YOUR_ACCOUNT "vsc-library/slurm templates/transfer.slurm" /absolute/source /absolute/destination

It copies contents and does not delete source or destination files. It does
not preserve timestamps, because the Leuven scratch cleanup can treat staged
files with old preserved timestamps as inactive. A rerun therefore skips every
file already present under its final name and never updates or overwrites one;
use a fresh destination when the source changed. Interrupted files are held in
a .rsync-partial directory rather than appearing complete. Symlinks within the
source tree are kept as links; links pointing outside it are copied as the
files they reference. It does not prove that the copies are complete enough
for your application; verify inputs before compute.
Do not copy a live database as though it were an immutable completed artifact.

Run the interactive helper from a login shell:

    bash "vsc-library/slurm templates/interactive.sh" YOUR_ACCOUNT wice

## Checkpoint contract

The application must handle USR1 by writing a complete compatible checkpoint
to durable storage, then exit with status 85. Its normal invocation must
resume that checkpoint automatically. The wrapper does not implement model
serialization, locking or checkpoint validation for the application.

    sbatch --account=YOUR_ACCOUNT "vsc-library/slurm templates/checkpoint.slurm" "$PWD" /absolute/path/to/python 0 -m your_package.train

The third argument 0 disables the wrapper's automatic requeue. A value from
1 to 10 permits at most that many automatic restarts after a confirmed
checkpoint status. The wrapper never requeues an ordinary failure or an
unconfirmed checkpoint. Because the script sets --requeue, Slurm itself may
also requeue the job, for example after a node failure. The wrapper cannot
bound those restarts, but they increase SLURM_RESTART_COUNT and so consume
the same budget. With limit 0, also pass --no-requeue to sbatch to forbid them.
Logs are opened in append mode, so each restart adds to the same job log.
Adapt the default CPU resources to a GPU allocation only when the application
and resume contract have been tested.

The initial log names are literal paths in the submission directory. If you
move them to a directory, create it before sbatch. Do not use ordinary shell
variables in SBATCH directives. Do not locate helper files relative to the
spooled batch-script path.

Read [Slurm guidance](../guides/SLURM.md), [storage](../guides/STORAGE.md),
[software](../guides/SOFTWARE.md) and [credits](../guides/OPERATIONS.md).
Project-specific modifications belong in parent scripts and docs/VSC.md;
do not edit these shared files from a submodule checkout.
