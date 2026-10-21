#!/bin/bash -l
#SBATCH --job-name=gpu_b200
#SBATCH --clusters=mindwell
#SBATCH --account=REPLACE_ME
#SBATCH --partition=gpu_b200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=60000M
#SBATCH --time=00:15:00
#SBATCH --gpus-per-node=1
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err
set -euo pipefail
source "${SLURM_SUBMIT_DIR:?}/vsc-library/slurm templates/environment.sh" "$@"
shift 2
[[ $# -gt 0 ]] || { echo "Provide Python arguments after PROJECT_ROOT and PYTHON." >&2; exit 2; }
nvidia-smi
exec "$PYTHON" "$@"
