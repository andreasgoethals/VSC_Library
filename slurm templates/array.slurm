#!/bin/bash -l
#SBATCH --job-name=array
#SBATCH --clusters=wice
#SBATCH --account=REPLACE_ME
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=13600M
#SBATCH --time=01:00:00
#SBATCH --array=0-9%2
#SBATCH --output=slurm-%x-%A_%a.out
#SBATCH --error=slurm-%x-%A_%a.err
set -euo pipefail
source "${SLURM_SUBMIT_DIR:?}/vsc-library/slurm templates/environment.sh" "$@"
shift 2
[[ $# -gt 0 ]] || { echo "Provide Python arguments after PROJECT_ROOT and PYTHON." >&2; exit 2; }
echo "Array index: ${SLURM_ARRAY_TASK_ID:?}; application must use it to select unique work/output."
exec "$PYTHON" "$@"
