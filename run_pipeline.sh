#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------
# check arguments
# -------------------------------------------------------------
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <problem1.pddl> <problem2.pddl> ..."
    exit 1
fi

PROBLEMS=("$@")

LP_FILES=()
ROLE_FILES=()

OUTPUT_DIR="$(dirname "${PROBLEMS[0]}")"
OUTPUT_TXT="$OUTPUT_DIR/results.txt"

# -------------------------------------------------------------
# generate ASP + role for each PDDL problem
# -------------------------------------------------------------
for PROBLEM_PDDL in "${PROBLEMS[@]}"; do
    if [[ "$PROBLEM_PDDL" != *.pddl ]]; then
        echo "Skipping non-PDDL file: $PROBLEM_PDDL"
        continue
    fi

    echo "Processing $PROBLEM_PDDL"

    BASE="${PROBLEM_PDDL%.pddl}"
    PROBLEM_LP="${BASE}.lp"
    ROLE_LP="${BASE}-role.lp"

    python Generate_ASP_State_Space.py "$PROBLEM_PDDL"
    python Generate_Roles.py "$PROBLEM_LP"

    LP_FILES+=("$PROBLEM_LP")
    ROLE_FILES+=("$ROLE_LP")
done

# -------------------------------------------------------------
# write PDDL inputs header
# -------------------------------------------------------------
{
  echo "PDDL INPUT PROBLEMS:"
  for p in "${PROBLEMS[@]}"; do
      [[ "$p" == *.pddl ]] && echo "  $p"
  done
  echo "----------------------------------------"
} > "$OUTPUT_TXT"

# -------------------------------------------------------------
# run clingo on all generated files
# -------------------------------------------------------------
clingo auxiliary.lp dl.lp \
       "${LP_FILES[@]}" \
       "${ROLE_FILES[@]}" \
  | tee /dev/tty \
  | python last_answer_set.py \
  | python asp2table.py >> "$OUTPUT_TXT"

echo "Pipeline completed."
echo "Results written to $OUTPUT_TXT"
