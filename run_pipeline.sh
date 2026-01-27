#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------
# check arguments
# -------------------------------------------------------------
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 [CLINGO_OPTIONS] <problem1.pddl> <problem2.pddl> ..."
    echo ""
    echo "Examples:"
    echo "  $0 problem1.pddl problem2.pddl"
    echo "  $0 --time-limit=60 problem1.pddl"
    echo "  $0 -n 0 --opt-mode=optN problem1.pddl problem2.pddl"
    exit 1
fi

# -------------------------------------------------------------
# separate clingo options from PDDL files
# -------------------------------------------------------------
CLINGO_OPTS=()
PROBLEMS=()

for arg in "$@"; do
    if [[ "$arg" == *.pddl ]]; then
        PROBLEMS+=("$arg")
    else
        CLINGO_OPTS+=("$arg")
    fi
done

# Check if we have at least one PDDL file
if [ "${#PROBLEMS[@]}" -eq 0 ]; then
    echo "Error: No PDDL files provided"
    echo "Usage: $0 [CLINGO_OPTIONS] <problem1.pddl> <problem2.pddl> ..."
    exit 1
fi

LP_FILES=()
ROLE_FILES=()

OUTPUT_DIR="$(dirname "${PROBLEMS[0]}")"
OUTPUT_TXT="$OUTPUT_DIR/results.txt"

# -------------------------------------------------------------
# generate ASP + role for each PDDL problem
# -------------------------------------------------------------
for PROBLEM_PDDL in "${PROBLEMS[@]}"; do
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
      echo "  $p"
  done
  echo ""
  if [ "${#CLINGO_OPTS[@]}" -gt 0 ]; then
      echo "CLINGO OPTIONS:"
      echo "  ${CLINGO_OPTS[*]}"
      echo ""
  fi
  echo "----------------------------------------"
} > "$OUTPUT_TXT"

# -------------------------------------------------------------
# run clingo on all generated files
# -------------------------------------------------------------
echo "Running clingo with options: ${CLINGO_OPTS[*]}"

clingo "${CLINGO_OPTS[@]}" \
       auxiliary.lp dl.lp \
       "${LP_FILES[@]}" \
       "${ROLE_FILES[@]}" \
  | tee /dev/tty \
  | python last_answer_set.py \
  | python asp2table.py >> "$OUTPUT_TXT"

echo "Pipeline completed."
echo "Results written to $OUTPUT_TXT"