#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------
# argument check
# -------------------------------------------------------------
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <problem.pddl> [text]"
    exit 1
fi

PROBLEM_PDDL="$1"
INPUT_TEXT="${2:-}"

OUTPUT_TXT="${PROBLEM_PDDL%.pddl}.txt"
PROBLEM_LP="${PROBLEM_PDDL%.pddl}.lp"
ROLE_LP="${PROBLEM_PDDL%.pddl}-role.lp"

mkdir -p "$(dirname "$OUTPUT_TXT")"

# -------------------------------------------------------------
# pipeline
# -------------------------------------------------------------

python Generate_ASP_State_Space_with_distance.py "$PROBLEM_PDDL"
python Generate_Roles.py "$PROBLEM_LP"

# -------------------------------------------------------------
# clingo invocation (conditionally add text)
# -------------------------------------------------------------
CLINGO_CMD=(clingo auxiliary.lp dl.lp "$PROBLEM_LP" "$ROLE_LP")

if [ -n "$INPUT_TEXT" ]; then
    CLINGO_CMD+=($INPUT_TEXT)
fi

"${CLINGO_CMD[@]}" \
  | tee /dev/tty \
  | python last_answer_set.py \
  | python asp2table.py > "$OUTPUT_TXT"

echo "Pipeline completed successfully."
