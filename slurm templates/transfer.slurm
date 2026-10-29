#!/bin/bash -l
#SBATCH --job-name=storage-transfer
#SBATCH --clusters=wice
#SBATCH --account=REPLACE_ME
#SBATCH --partition=interactive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err
# Use partition-default memory with --cpus-per-task; see guides/SLURM.md.
set -euo pipefail
source_dir="${1:?Usage: sbatch transfer.slurm ABSOLUTE_SOURCE_DIR ABSOLUTE_DEST_DIR}"
destination="${2:?Provide the absolute destination directory}"
[[ "$source_dir" == /* && -d "$source_dir" && "$destination" == /* && "$destination" != / ]] || {
    echo "Expected an existing absolute source and a non-root absolute destination." >&2; exit 2;
}
source_dir="$(realpath "$source_dir")"
[[ "$source_dir" != / ]] || { echo "Refusing to copy a filesystem root." >&2; exit 2; }
mkdir -p "$destination"
destination="$(realpath "$destination")"
[[ "$destination" != / ]] || { echo "Refusing a filesystem-root destination." >&2; exit 2; }
[[ "$destination" != "$source_dir" && "$destination"/ != "$source_dir"/* ]] || {
    echo "Destination must not be the source or inside it." >&2; exit 2;
}
# No deletion and no timestamp preservation: the Leuven scratch cleanup treats
# old preserved timestamps as inactive files (source: kuleuven_storage.rst).
# Retries skip files that already exist under their final name instead of
# relying on timestamps. rsync only gives a file its final name once complete;
# an interrupted file is held in .rsync-partial and transferred again next run.
# Consequence: an existing destination file is never updated or overwritten.
# Symlinks inside the source tree stay links; links pointing outside it are
# copied as the files they reference, so the destination is self-contained.
# Choose destination storage before submission; do not run on P100/V100 for GPFS.
rsync -r --links --copy-unsafe-links --ignore-existing --partial-dir=.rsync-partial \
    --info=stats2 -- "$source_dir"/ "$destination"/
echo "Copy complete. Verify the destination before starting compute or removing any source."
