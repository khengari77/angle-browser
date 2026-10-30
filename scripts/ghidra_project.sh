#!/usr/bin/env bash
set -euo pipefail
root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
launcher="$root_dir/.local-tools/ghidra_12.1.4_PUBLIC/support/analyzeHeadless"
project_dir="$root_dir/artifacts/ghidra-projects"
mkdir -p "$project_dir"
case "${1:-}" in
  import)
    if [[ -e "$project_dir/ArcPreservation.gpr" ]]; then
      echo 'Project already exists; use the targets command to resume.' >&2
      exit 1
    fi
    exec "$launcher" "$project_dir" ArcPreservation -import "$root_dir/artifacts/macos/Arc.x86_64" -noanalysis
    ;;
  targets)
    if [[ $# -lt 4 ]]; then echo 'Usage: ghidra_project.sh targets NEW_OUTPUT_DIR START END_EXCLUSIVE [START END_EXCLUSIVE ...]' >&2; exit 2; fi
    shift
    output_dir="$1"
    "$launcher" "$project_dir" ArcPreservation -process Arc.x86_64 -noanalysis -scriptPath "$root_dir/scripts/ghidra" -postScript ArcTargeted.java "$@"
    python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p.get("batch_completed"), "Incomplete Ghidra script output"' "$output_dir/report.json"
    ;;
  tables)
    if [[ $# -ne 3 ]]; then echo 'Usage: ghidra_project.sh tables MANIFEST NEW_REPORT_FILE' >&2; exit 2; fi
    "$launcher" "$project_dir" ArcPreservation -process Arc.x86_64 -noanalysis -scriptPath "$root_dir/scripts/ghidra" -postScript ArcJumpTables.java "$2" "$3"
    python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p.get("tables"), "Missing Ghidra table report"' "$3"
    ;;
  *) echo 'Usage: ghidra_project.sh import | targets NEW_OUTPUT_DIR START END_EXCLUSIVE ...' >&2; exit 2 ;;
esac
