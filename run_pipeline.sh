#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------
# helpers
# -------------------------------------------------------------
run() {
    echo "> $*"
    "$@"
}

# -------------------------------------------------------------
# argument check
# -------------------------------------------------------------
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <problem.pddl>"
    exit 1
fi

# -------------------------------------------------------------
# paths
# -------------------------------------------------------------
PROBLEM_PDDL="$1"

# Output payh
OUTPUT_TXT="${PROBLEM_PDDL%.pddl}.txt"

# Derived intermediate filenames
PROBLEM_LP="${PROBLEM_PDDL%.pddl}.lp"
ROLE_LP="${PROBLEM_PDDL%.pddl}-role.lp"

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_TXT")"

# -------------------------------------------------------------
# pipeline
# -------------------------------------------------------------

# 1) Generate ASP state space
run python Generate_ASP_State_Space.py "$PROBLEM_PDDL"

# 2) Generate roles
run python Generate_Roles.py "$PROBLEM_LP"

# 3) Compute generalized plan
echo "> clingo run.lp dl.lp $PROBLEM_LP $ROLE_LP | tee /dev/tty | python asp2table.py > $OUTPUT_TXT"
clingo run.lp dl.lp "$PROBLEM_LP" "$ROLE_LP" | tee /dev/tty | python last_answer_set.py | python asp2table.py > "$OUTPUT_TXT"

# -------------------------------------------------------------
# done
# -------------------------------------------------------------
echo
echo "Pipeline completed successfully."
echo "Result written to: $OUTPUT_TXT"
