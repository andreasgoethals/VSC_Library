#!/bin/bash -l
#SBATCH --job-name=multi_gpu
#SBATCH --clusters=wice
#SBATCH --account=REPLACE_ME
#SBATCH --partition=gpu_a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=160000M
#SBATCH --time=00:30:00
#SBATCH --gpus-per-node=4
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err
set -euo pipefail
source "${SLURM_SUBMIT_DIR:?}/vsc-library/slurm templates/environment.sh" "$@"
shift 2
[[ $# -gt 0 ]] || { echo "Provide Python arguments after PROJECT_ROOT and PYTHON." >&2; exit 2; }
nvidia-smi
gpus="${SLURM_GPUS_ON_NODE:?}"
[[ "$gpus" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid GPU count: $gpus" >&2; exit 2; }
# torchrun keeps an inherited OMP_NUM_THREADS for every worker, so divide the
# allocation's CPUs between the per-GPU workers instead of giving each all of them.
worker_threads=$(( ${SLURM_CPUS_PER_TASK:-1} / gpus ))
(( worker_threads >= 1 )) || worker_threads=1
export OMP_NUM_THREADS="$worker_threads" MKL_NUM_THREADS="$worker_threads"
export OPENBLAS_NUM_THREADS="$worker_threads" BLIS_NUM_THREADS="$worker_threads"
export NUMEXPR_NUM_THREADS="$worker_threads"
echo "torchrun workers: $gpus; threads per worker: $worker_threads"
# Application must implement DDP and honor LOCAL_RANK; one node only.
exec "$PYTHON" -m torch.distributed.run --standalone --nnodes=1 \
    --nproc-per-node="$gpus" "$@"
