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

For conda, the official recommendation, barring special requirements, is a
centrally installed Miniforge3 module (for example Miniforge3/25.3.0-3): its
base is shared, cannot be modified and by default uses only the conda-forge
channel. Load it and source its conda.sh rather than running conda init bash,
which would enable conda in every shell. Configure, once, environments in
VSC_DATA and the package cache in VSC_SCRATCH instead of the HOME defaults:

    conda config --append envs_dirs $VSC_DATA/conda_envs
    conda config --append pkgs_dirs $VSC_SCRATCH/conda_pkgs

Conda packages generally cannot be combined with software modules.

For pip-based environments on top of modules, the vsc-venv module creates and
activates a per-architecture virtual environment from a requirements.txt and
an optional modules.txt, and reloads the same modules on each activation:

    module load vsc-venv
    source vsc-venv --activate --requirements requirements.txt --modules modules.txt
    source vsc-venv --deactivate

Its environments are created in a venvs subdirectory of the current directory.

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
quota. The helper creates per-job temporary caches on node-local
VSC_SCRATCH_NODE, which is removed when the job ends, falling back to native
VSC_SCRATCH, where finished jobs' cache directories remain until removed.
Those caches are disposable. For single-node torchrun, the multi-GPU template
divides the allocated CPUs between the per-GPU workers' thread limits. Stage needed model files separately; do not rely
on an empty cache being able to download during the job. Persistent environments
and irreplaceable model assets need project-defined durable locations.

Profile CPU parsing, tokenization, data loading and filesystem waits when a
GPU is idle. More GPUs do not accelerate those stages automatically.

## Containers and distributed software

Docker is generally not available; VSC clusters use Apptainer (formerly
Singularity), which runs SIF images without root. Prefer an existing module
when one exists; containers suit hard-to-install, legacy or externally developed
software. Essentials from the official source:

- Point the cache and temporary directories away from HOME before use. The
  source recommends adding to ~/.bashrc:

      export APPTAINER_CACHEDIR=/tmp/$USER/apptainer_cachedir
      export APPTAINER_TMPDIR=/tmp/$USER/apptainer_tmpdir
      mkdir -p $APPTAINER_TMPDIR

- Build and run on a compute node with enough RAM; store the large images
  where you have quota, for example VSC_DATA.
- apptainer pull NAME.sif docker://IMAGE:TAG converts a registry image; prefer
  verified publishers and know what an image contains.
- apptainer exec, run and shell execute a command, the runscript or a shell.
  HOME and the current directory are bound by default; add others with
  -B, for example -B $VSC_SCRATCH. Host environment variables pass in, which
  can interfere (use --cleanenv when needed).
- Images are immutable: bind a host directory or use --writable-tmpfs for
  applications that write inside the image.
- Many images can be built without root using --fakeroot
  (apptainer build --fakeroot IMAGE.sif DEFINITION.def); some builds fail
  because of fakeroot limitations and must be built elsewhere.
- NVIDIA GPUs need apptainer run --nv (or exec --nv). The container's CUDA
  build must match the host GPU and driver; the source recommends a CUDA
  version matching an available CUDA module and a container OS of a similar
  generation to the host.

Record image hashes and bind only the required paths. Containers do not bypass
Slurm allocations or storage rules, and MPI inside a container needs an MPI
library compatible with the host.

For MPI, Leuven recommends the MPI implementation's launcher, typically mpirun.
The reviewed Slurm installation lacks PMI support, so an MPI program launched
through srun can hang. Follow the current site-specific guidance.
The 29 October 2026 source also warns that explicit memory combined with
`--cpus-per-task` can make CPU allocation variables disagree and fail `srun`
or `mpirun`. See [the resource-request workaround](SLURM.md#explicit-memory-and-cpu-requests).
Single-node torchrun has a separate template; a multi-node PyTorch program
needs its own tested launch/rendezvous and network setup.

Sources: source/leuven/slurm_specifics.rst,
source/leuven/mindwell_quick_start.rst,
source/leuven/wice_advanced_guide.rst,
source/compute/software/installing_software/containers.rst,
source/compute/software/installing_software/conda_based_managers.rst and
source/compute/software/installing_software/python_package_management.rst.
