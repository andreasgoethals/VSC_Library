#!/bin/bash -l
#SBATCH --job-name=storage-transfer
#SBATCH --clusters=wice
#SBATCH --account=REPLACE_ME
#SBATCH --partition=interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=6800M
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err
set -euo pipefail
source_dir="${1:?Usage: sbatch transfer.slurm ABSOLUTE_SOURCE_DIR ABSOLUTE_DEST_DIR}"
destination="${2:?Provide the absolute destination directory}"
[[ "$source_dir" == /* && -d "$source_dir" && "$destination" == /* && "$destination" != / ]] || {
    echo "Expected an existing absolute source and a non-root absolute destination." >&2; exit 2;
}
source_dir="$(realpath "$source_dir")"
mkdir -p "$destination"
destination="$(realpath "$destination")"
[[ "$destination" != "$source_dir" && "$destination"/ != "$source_dir"/* ]] || {
    echo "Destination must not be the source or inside it." >&2; exit 2;
}
# No deletion and no timestamp preservation: appropriate for initial scratch staging.
# Choose destination storage before submission; do not run on P100/V100 for GPFS.
rsync -r --partial --info=stats2 -- "$source_dir"/ "$destination"/
echo "Copy complete. Verify the destination before starting compute or removing any source."
