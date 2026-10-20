#!/bin/bash -l
#SBATCH --job-name=checkpoint-example
#SBATCH --clusters=wice
#SBATCH --account=REPLACE_ME
#SBATCH --partition=batch
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=13600M
#SBATCH --time=02:00:00
#SBATCH --signal=B:USR1@300
#SBATCH --requeue
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err
set -euo pipefail
source "${SLURM_SUBMIT_DIR:?}/vsc-library/slurm templates/environment.sh" "$@"
shift 2
max_restarts="${1:?Third argument is maximum automatic restarts (0 disables requeue)}"
shift
[[ "$max_restarts" =~ ^[0-9]+$ && "$max_restarts" -le 10 ]] || {
    echo "Choose a restart limit from 0 to 10." >&2; exit 2;
}
[[ $# -gt 0 ]] || { echo "Provide the application's Python arguments." >&2; exit 2; }
# Application contract:
# USR1 -> save a complete checkpoint to persistent storage -> exit status 85.
# The same invocation must find and resume that complete checkpoint on restart.
# Never use 85 for ordinary failure or for an incomplete checkpoint.
checkpoint_requested=0
"$PYTHON" "$@" &
child=$!
request_checkpoint() {
    checkpoint_requested=1
    kill -USR1 "$child" 2>/dev/null || true
}
trap request_checkpoint USR1
status=0
wait "$child" || status=$?
if (( checkpoint_requested )); then
    # The first wait may have been interrupted by the signal. Wait for the
    # application's actual exit, ignoring duplicate notifications.
    trap '' USR1
    status=0
    wait "$child" || status=$?
fi
if (( checkpoint_requested && status == 85 )); then
    restarts="${SLURM_RESTART_COUNT:-0}"
    if (( restarts < max_restarts )); then
        echo "Application confirmed a complete checkpoint; requesting a bounded requeue."
        scontrol --clusters="${SLURM_CLUSTER_NAME:?}" requeue "$SLURM_JOB_ID"
        exit 0
    fi
    echo "Checkpoint saved; automatic requeue disabled or restart limit reached." >&2
fi
exit "$status"
