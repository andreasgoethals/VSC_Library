#!/bin/bash -l
#SBATCH --job-name=cpu_mindwell
#SBATCH --clusters=mindwell
#SBATCH --account=REPLACE_ME
#SBATCH --partition=batch_graniterapids
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err
# Use partition-default memory with --cpus-per-task; see guides/SLURM.md.
set -euo pipefail
source "${SLURM_SUBMIT_DIR:?}/vsc-library/slurm templates/environment.sh" "$@"
shift 2
[[ $# -gt 0 ]] || { echo "Provide Python arguments after PROJECT_ROOT and PYTHON." >&2; exit 2; }
exec "$PYTHON" "$@"
