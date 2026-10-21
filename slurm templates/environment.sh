#!/bin/bash
# Sourced by the examples; the parent project owns any activation/module hook.
set -euo pipefail
PROJECT_ROOT="${1:?First argument must be the absolute project checkout path}"
PYTHON="${2:?Second argument must be an absolute environment Python executable}"
[[ "$PROJECT_ROOT" == /* && -d "$PROJECT_ROOT" ]] || {
    echo "Project root must be an existing absolute directory." >&2; return 2;
}
[[ "$PYTHON" == /* ]] || {
    echo "Use an absolute interpreter path; do not rely on inherited activation." >&2; return 2;
}
cd "$PROJECT_ROOT"
if [[ -f scripts/vsc_environment.sh ]]; then
    # This optional file belongs to the parent project, outside the submodule.
    # module load and conda activate scripts can reference unset variables,
    # so nounset is relaxed only while the hook runs and then restored.
    set +u
    source scripts/vsc_environment.sh
    set -euo pipefail
fi
[[ -x "$PYTHON" ]] || { echo "Requested Python is not executable: $PYTHON" >&2; return 2; }
threads="${SLURM_CPUS_PER_TASK:-1}"
[[ "$threads" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid CPU count." >&2; return 2; }
export OMP_NUM_THREADS="$threads" MKL_NUM_THREADS="$threads"
export OPENBLAS_NUM_THREADS="$threads" BLIS_NUM_THREADS="$threads" NUMEXPR_NUM_THREADS="$threads"
export OMP_MAX_ACTIVE_LEVELS=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
: "${VSC_SCRATCH:?Native cluster scratch must be available}"
: "${SLURM_JOB_ID:?Run inside a Slurm allocation}"
# Prefer node-local scratch: Slurm removes it when the job ends, so caches do
# not accumulate. Fall back to native scratch, where old per-job directories
# remain until removed by the user or the scratch access-time cleanup.
if [[ -n "${VSC_SCRATCH_NODE:-}" && -d "$VSC_SCRATCH_NODE" && -w "$VSC_SCRATCH_NODE" ]]; then
    cache_root="$VSC_SCRATCH_NODE"
else
    cache_root="$VSC_SCRATCH"
fi
cache="$cache_root/vsc-library-cache/${SLURM_ARRAY_JOB_ID:-$SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID:-single}_${SLURM_RESTART_COUNT:-0}"
export XDG_CACHE_HOME="$cache" HF_HOME="$cache/huggingface" TORCH_HOME="$cache/torch"
export TRITON_CACHE_DIR="$cache/triton" CUDA_CACHE_PATH="$cache/nvidia"
export PIP_CACHE_DIR="$cache/pip" MPLCONFIGDIR="$cache/matplotlib"
mkdir -p "$HF_HOME" "$TORCH_HOME" "$TRITON_CACHE_DIR" "$CUDA_CACHE_PATH" "$PIP_CACHE_DIR" "$MPLCONFIGDIR"
echo "Job: $SLURM_JOB_ID Cluster: ${SLURM_CLUSTER_NAME:-unknown} Partition: ${SLURM_JOB_PARTITION:-unknown}"
echo "Node: $(hostname) CPUs: $threads UTC: $(date -u +%FT%TZ)"
echo "Project commit: $(git rev-parse HEAD 2>/dev/null || echo unavailable)"
echo "VSC Library pin: $(git -C vsc-library rev-parse HEAD 2>/dev/null || echo unavailable)"
echo "Interpreter: $PYTHON"
echo "Temporary caches: $cache"
"$PYTHON" --version
# These caches are temporary. Stage weights/inputs explicitly before compute.
