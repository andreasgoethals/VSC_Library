#!/bin/bash -l
#SBATCH --job-name=gpu_debug
#SBATCH --clusters=wice
#SBATCH --account=REPLACE_ME
#SBATCH --partition=gpu_a100_debug
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=28000M
#SBATCH --time=00:10:00
#SBATCH --gpus-per-node=1
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err
set -euo pipefail
source "${SLURM_SUBMIT_DIR:?}/vsc-library/slurm templates/environment.sh" "$@"
shift 2
[[ $# -gt 0 ]] || { echo "Provide Python arguments after PROJECT_ROOT and PYTHON." >&2; exit 2; }
nvidia-smi
exec "$PYTHON" "$@"
