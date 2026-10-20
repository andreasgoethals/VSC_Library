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
#SBATCH --output=slurm-%x-%A-%a.out
#SBATCH --error=slurm-%x-%A-%a.err
set -euo pipefail
source "${SLURM_SUBMIT_DIR:?}/vsc-library/slurm templates/environment.sh" "$@"
shift 2
[[ $# -gt 0 ]] || { echo "Provide Python arguments after PROJECT_ROOT and PYTHON." >&2; exit 2; }
nvidia-smi
# Application must implement DDP and honor LOCAL_RANK; one node only.
exec "$PYTHON" -m torch.distributed.run --standalone --nnodes=1 \
    --nproc-per-node="${SLURM_GPUS_ON_NODE:?}" "$@"
