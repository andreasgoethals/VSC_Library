#!/bin/bash
# Run from a Leuven login shell, after inspecting current site availability.
set -euo pipefail
account="${1:?Usage: bash interactive.sh CREDIT_ACCOUNT [wice|mindwell]}"
cluster="${2:-wice}"
[[ "$cluster" == wice || "$cluster" == mindwell ]] || { echo "Unknown cluster" >&2; exit 2; }
exec srun --account="$account" --clusters="$cluster" --partition=interactive \
    --nodes=1 --ntasks=1 --cpus-per-task=2 --time=01:00:00 --pty bash -l
