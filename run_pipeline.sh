#!/usr/bin/env bash
set -euo pipefail

# ---- helpers -------------------------------------------------

die() {
  echo "Error: $*" >&2
  exit 1
}

run() {
  echo "> $*"
  "$@"
}

# ---- checks --------------------------------------------------

if [[ $# -ne 1 ]]; then
  die "Usage: ./run_pipeline.sh /path/to/problem.pddl"
fi

if ! command -v python >/dev/null 2>&1; then
  die "python not found (is your conda environment activated?)"
fi

if ! command -v clingo >/dev/null 2>&1; then
  die "clingo not found in the current conda environment"
fi

# ---- paths ---------------------------------------------------

PROBLEM_PDDL="$(realpath "$1")"
WORKDIR="$(dirname "$PROBLEM_PDDL")"
STEM="$(basename "$PROBLEM_PDDL" .pddl)"

PROBLEM_LP="$WORKDIR/$STEM.lp"
ROLE_LP="$WORKDIR/$STEM-role.lp"
OUTPUT_TXT="$WORKDIR/output.txt"

# ---- pipeline ------------------------------------------------

# 1) Generate search space
run python Generate_ASP_State_Space.py "$PROBLEM_PDDL"

# 2) Generate roles
run python Generate_Roles.py "$PROBLEM_LP"

# 3) Compute generalized plan
echo "> clingo ... | python asp2table.py"
clingo run.lp dl.lp "$PROBLEM_LP" "$ROLE_LP" | python asp2table.py > "$OUTPUT_TXT"

echo
echo "Pipeline completed successfully."
echo "Result written to: $OUTPUT_TXT"
