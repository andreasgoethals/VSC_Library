# Slurm submission, monitoring and resume

## Describe the workload explicitly

Use one task with several CPUs for an ordinary threaded Python process.
Use several tasks when the program really launches cooperating processes.
An array represents independent tasks with distinct input/configuration IDs.
GPU count is separate from the CPU task count.

At Leuven, explicitly select the cluster even though the login-node default
for queries is wICE. Use an authorized credit account, real partition,
measured memory and a realistic walltime. Start a small pilot before a large grid.

Examples, to adapt in a consuming repository:

    sbatch --account=YOUR_ACCOUNT --clusters=wice "vsc-library/slurm templates/cpu.slurm" "$PWD" /absolute/path/to/python -m your_package.prepare
    sbatch --account=YOUR_ACCOUNT --clusters=mindwell "vsc-library/slurm templates/gpu_b200.slurm" "$PWD" /absolute/path/to/python -m your_package.train

Submit from the consuming repository root. The examples use a vsc-library
mountpoint and read any project environment hook from scripts/vsc_environment.sh.
No account or interpreter is supplied automatically by the library.

SBATCH directives are parsed before the Bash body. They do not expand ordinary
shell variables. Templates use simple relative log names in the submission
directory so Slurm can open the initial logs before any code runs.
Create custom log directories before submission; creating them later in the job
does not fix a failed initial output-file open.

Leuven does not normally inherit all submission-shell variables. The templates
pass project paths and the interpreter as positional arguments. Where an
environment variable really must be exported, follow the site's documented
minimal-environment syntax; use export=ALL only when inheriting the whole
submission environment is deliberate and checked.

## Explicit memory and CPU requests

The official Leuven scheduler documentation updated on 29 October 2026 warns
that combining an explicit memory request with `--cpus-per-task` can leave
`SLURM_CPUS_PER_TASK` and `SLURM_TRES_PER_TASK` inconsistent when memory causes
Slurm to allocate extra cores. `srun` and `mpirun` then fail. Its documented
workaround is to omit `--cpus-per-task` when explicitly requesting memory.

The supplied templates retain their CPU requests and use partition-default
memory, with no explicit `--mem` or `--mem-per-cpu`. Inspect the partition's
`DefMemPerCPU`/limits and the allocated memory before choosing a workload;
the old templates' fixed memory amounts are no longer requested. Increase the
CPU request to obtain more memory at the partition default, respecting GPU/core
limits, and estimate the resulting cost with `sam-quote`.

If your project needs explicit memory, remove the template's `--cpus-per-task`
directive first and verify the resulting CPU allocation and thread budget.
Do not add a command-line memory override to these unchanged templates.
An omitted CPU setting also changes how the environment helper chooses its
thread count; inspect the job's allocation before selecting workers.

## Monitor the right cluster

    squeue --clusters=all --me
    sinfo --clusters=wice
    sinfo --clusters=mindwell
    scontrol --clusters=mindwell show job JOB_ID
    sacct --clusters=all -j JOB_ID --format=JobID,JobName,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
    slurm_jobinfo JOB_ID
    slurmtop

Use an actual job identifier in place of JOB_ID. Accounting memory can appear
on job-step rows and may be sampled; it is not a continuous profiler. Compare
allocated resources with application measurements and record code/input identity.

Pending is not a failed run. Inspect the reason: priority/resources, maintenance,
reservation, account balance, QoS or dependency. Resubmitting duplicates usually
does not resolve the underlying restriction. Some QoS limits constrain all
submitted active jobs, while others constrain resources in running jobs.

Cancel only a job you intend to cancel, with its explicit cluster and ID:

    scancel --clusters=mindwell JOB_ID

Do not cancel a whole user's workload as a generic troubleshooting step.

## Arrays and dependencies

The array template sets a small concurrency limit and exposes
SLURM_ARRAY_TASK_ID to the application. Give each task a unique output
namespace. A completed file alone is not proof of a valid finished task;
check its expected schema, code/configuration identity and completion marker.

For a same-cluster pipeline, submit the next job with
--dependency=afterok:JOB_ID. Capture the numeric ID from sbatch --parsable;
multi-cluster output can also include a semicolon and cluster name.
The dependency must refer to the correct cluster's job. Cross-cluster
dependency behavior should be verified with VSC rather than assumed.
Transfers and preprocessing can be separate allocations so a GPU does not
wait while expensive CPU preparation happens.

## Checkpoints and walltime

Checkpoint the application state, RNG state and relevant data/order position
periodically, using atomic replacement and a manifest/pointer written last.
Resume only from a complete compatible checkpoint. Verify completed outputs
before repeating expensive work.

A Slurm signal is a notification, not a checkpoint implementation. The
checkpoint template forwards USR1 to a background Python process. The
application must handle it, save a durable checkpoint and exit with its
documented checkpoint status. Only that confirmed status permits a requeue.
An application without this handler will not become resumable by copying a
shell template.

The template requires explicit opt-in to automatic requeue and a restart
limit. Requeue policy is site-dependent and every resumed allocation can
consume credits. A normal application failure must remain a failure.

## Efficiency and evidence

Keep batch jobs short enough for scheduling where practical, but leave enough
time for initialization and checkpoint saving. Measure allocated host memory,
CPU workers, GPU utilization and storage waits on representative inputs.
Use the [credits guide](OPERATIONS.md) to estimate cost before expanding a sweep.
Log the project commit, VSC Library pin, environment, input/configuration
fingerprints, job ID, cluster, resources, outcome and artifact locations.

Sources: source/compute/jobs/clusters_slurm.rst,
source/leuven/slurm_specifics.rst, source/leuven/wice_quick_start.rst and
source/leuven/mindwell_quick_start.rst.
