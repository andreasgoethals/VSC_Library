# Software and reproducible environments

## Modules and architecture

Load the required modules inside each job, using the site's login-shell
initialization. Avoid automatically loading application modules or activating
environments in .bashrc. The selected node architecture determines which
module tree and compiled libraries are appropriate.

Use module avail, module spider and module help to inspect availability.
The OnDemand Module Browser is another index of centrally installed modules,
not a complete list of packages inside every interpreter.

VSC_ARCH_LOCAL, VSC_ARCH_SUFFIX and MODULEPATH describe the native architecture
and module view. The reviewed Mindwell source distinguishes the CPU 2024a and
GPU 2025a software stacks. Choose a module/environment from the actual target
node's available toolchain; do not copy a hard-coded module version from an
old project.

## Python, virtual environments and conda

Keep the interpreter and environment reproducible: record the module stack,
environment path, Python version, package lock/specification and code revision
in the project's own docs/VSC.md and run metadata.

An active virtualenv can shadow a newly activated conda environment. Always
inspect the executable actually running the job. The templates require an
explicit absolute interpreter path, rather than silently falling back to
system Python. That still requires an environment built with compatible
libraries and architecture.

If module loading or activation is needed, place it in the consuming project's
scripts/vsc_environment.sh. The template's helper sources that file before
checking the requested interpreter. Do not put a different project's settings
inside this library.

Build/install on a suitable allowed setup node or allocation according to site
policy. Do not install in a populated shared environment while another job is
using it. Stage network-dependent artifacts before compute; the presence of
internet access on a login node does not establish compute-node connectivity.

## CUDA, drivers and application kernels

The NVIDIA driver belongs to the host. A CUDA toolkit/runtime and the CUDA
support built into PyTorch or another application belong to different layers.
The CUDA version shown by nvidia-smi is not a report of every Python package's
runtime or supported device kernels.

Inside a GPU allocation, record nvidia-smi output, the interpreter, framework
version and its CUDA version. Check the selected device and run the actual
operations the application needs. Merely importing torch or seeing a GPU does
not prove compatibility with a B200, custom extension or specific precision.

Do not assume a driver maintenance announcement means that environments,
extensions, fused kernels or downloaded wheels were rebuilt for you.

## Threads, caches and input preparation

Bound numerical-library threads to the allocation. The helper sets OMP, MKL,
OpenBLAS, BLIS and NumExpr thread limits from SLURM_CPUS_PER_TASK and disables
nested OpenMP parallelism. Choose data-loader workers with the same CPU budget
in mind. An array of jobs each spawning a machine-sized thread pool can
oversubscribe the allocated cores.

Keep Hugging Face, PyTorch, Triton, CUDA and pip caches outside the small HOME
quota. The helper creates per-job temporary caches on native scratch.
Those caches are disposable. Stage needed model files separately; do not rely
on an empty cache being able to download during the job. Persistent environments
and irreplaceable model assets need project-defined durable locations.

Profile CPU parsing, tokenization, data loading and filesystem waits when a
GPU is idle. More GPUs do not accelerate those stages automatically.

## Containers and distributed software

The official source describes Apptainer/Singularity usage. Build and retain
images in an allowed setup workflow, record image hashes and bind only the
required paths. GPU containers still use the host driver and need compatible
CUDA/application binaries; they do not bypass Slurm allocations or storage rules.
Do not assume a privileged Docker daemon is available on compute nodes.

For MPI, Leuven recommends the MPI implementation's launcher, typically mpirun.
The reviewed Slurm installation lacks PMI support, so an MPI program launched
through srun can hang. Follow the current site-specific guidance.
Single-node torchrun has a separate template; a multi-node PyTorch program
needs its own tested launch/rendezvous and network setup.

Sources: source/leuven/slurm_specifics.rst,
source/leuven/mindwell_quick_start.rst,
source/leuven/wice_advanced_guide.rst and
source/compute/software/installing_software/containers.rst.
