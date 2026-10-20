#!/bin/bash -l
#SBATCH --job-name=cpu
#SBATCH --clusters=wice
#SBATCH --account=REPLACE_ME
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=27200M
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%A-%a.out
#SBATCH --error=slurm-%x-%A-%a.err
set -euo pipefail
source "${SLURM_SUBMIT_DIR:?}/vsc-library/slurm templates/environment.sh" "$@"
shift 2
[[ $# -gt 0 ]] || { echo "Provide Python arguments after PROJECT_ROOT and PYTHON." >&2; exit 2; }
exec "$PYTHON" "$@"
