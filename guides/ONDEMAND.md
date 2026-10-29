# KU Leuven Open OnDemand

[Open OnDemand](https://ondemand.hpc.kuleuven.be/) is a browser front end to
the same HPC service. It does not replace Slurm or provide unlimited resources.

## What each feature does

| Feature | Use |
|---|---|
| Files | Browse, upload, download, view and edit files; Leuven's menu exposes HOME and DATA |
| Clusters → Login (Server) Shell Access | A terminal on a shared login node |
| Jobs / Active Jobs | Inspect queued/running jobs; available actions depend on the portal |
| Interactive Apps | Submit a Slurm allocation and start an app inside it |
| My Interactive Sessions | Return to, connect to and end app sessions |
| Help | Support entry points, including the ticket option announced in October 2026 |

The Files editor has a Save button. The documented Ctrl+S behavior may save
the page locally rather than save the remote file; use the button and verify.
Browser transfers suit small files. For large transfers, use the supported
transfer tools described in [storage](STORAGE.md).

## Launch an application

1. Choose the app and the cluster/partition.
2. Select your credit account, time, CPU cores, host memory and GPU count.
   A GPU request only helps software that uses that GPU.
3. Set the working directory and any app-specific environment options.
4. Launch, wait for the queued allocation, then connect.
5. Save your work and delete/end the session when finished. Closing a browser
   tab alone is not reliable evidence that an allocation ended.

Resource requests determine queue time, node type and possible cost. OnDemand
applications can run on regular paid GPU/CPU partitions. The special interactive
partitions have their own smaller limits and Leuven documents them as free.
Check the selected partition and [hardware guide](CLUSTERS.md).

Do not confuse GPU device memory with the form's host RAM per core. Excess
host-memory requests can reserve additional cores. Match the installed Python/
toolchain and the environment expected by the project.

## JupyterLab

At Leuven the default top-level notebook directory is DATA; set the working
directory to another accessible filesystem when appropriate.
The pure-module option selects a consistent toolchain/Python and supplies its
Jupyter environment. Optional module checkboxes or a pre-run scriptlet can add
software. The source also describes supported personal virtual/conda environment
options; follow the current Leuven tab because these differ across portals.

Check the running kernel's interpreter and CUDA visibility inside the notebook.
Selecting a Python in a terminal does not necessarily change an existing kernel.
Keep outputs/checkpoints on the correct project filesystem. Do not install into
an unrelated shared environment from a notebook.

## VS Code, desktop and other apps

For editing in VS Code Server, Leuven recommends a single core on wICE's
interactive partition. A terminal opened inside VS Code runs on that app's node.
Use a suitable allocation for testing, debugging or GPU execution.

The source covers VS Code Server and Tunnel separately, including extension
caveats. It also covers desktop, interactive shell, RStudio Server, TensorBoard,
MATLAB, ParaView, PyCharm, Fluent, GaussView, IGV-Web and Open WebUI. Availability
depends on the portal and site. The complete instructions stay in the source
snapshot rather than being duplicated for every app.

Avoid requesting a production GPU just to keep an editor open. Do not expose
private data through session-sharing links or enter extension credentials into
tracked files. A view-only noVNC link still shares what is visible.

## Meaning of the October 2026 notice

The following release details come from the portal banner quoted by the owner.
The migration and default-cluster rules also appear in the official source.

- **GPU drivers updated:** the host software controlling NVIDIA GPUs changed.
  The notice does not identify a driver version. Your Python environment and
  its CUDA runtime are separate; inspect nvidia-smi and run the application's
  import/CUDA preflight inside an allocated GPU session before a long job.
- **P100/V100 moved from Genius to wICE:** select wICE and gpu_p100 or gpu_v100
  for those devices. Audit older submission scripts that still select Genius.
  They do not become A100/H100 devices, and the P100/V100 nodes still cannot
  access GPFS according to current Leuven storage documentation.
- **Default Slurm cluster is wICE:** unqualified queries on a login node refer
  to wICE. Use an explicit cluster for submissions; Leuven requires it.
  Query Mindwell explicitly or use the all-clusters option where supported.
- **Genius removed from the portal:** choose wICE/Mindwell. This removes an
  obsolete selection, not your research repository or datasets.
- **Credit dashboard:** view the balances of accounts you can access. The job's
  selected account and resources still control charging.
- **Help-menu tickets:** the announced support form provides a convenient way
  to report issues. Include the job ID, cluster, time and minimal error evidence,
  while removing credentials and private data.
- **Module Browser:** search centrally installed modules. The announced index
  does not yet list every R/Python/Julia/Perl/Rust extension. A missing search
  result does not prove that a package is unavailable. Check module help and the
  selected interpreter/environment.

The V100 incident link in the old banner is historical context. Check the
[live status page](https://status.vscentrum.be/tier2_leuven.html) for current
availability rather than treating that old notice as a permanent restriction.

For custom batch scripts or launches from an OnDemand shell, follow the
[explicit-memory/CPU warning](SLURM.md#explicit-memory-and-cpu-requests).
Do not assume a portal form and a hand-written Slurm script make identical
resource requests; inspect the generated job if its launcher fails.

Sources: source/compute/portal/index.rst,
source/compute/portal/ondemand/files.rst,
source/compute/portal/ondemand/login-shell.rst,
source/compute/portal/ondemand/interactive-apps.rst,
source/compute/portal/ondemand/jupyterlab.rst,
source/compute/portal/ondemand/vscode-server.rst,
source/leuven/slurm_specifics.rst and the owner-provided 1 October 2026 banner.
