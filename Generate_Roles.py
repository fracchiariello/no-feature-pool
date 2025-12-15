import subprocess
import re
import sys  # Add this import for sys.executable

# Define success codes for Clingo (adjust based on your needs)
CLINGO_SUCCESS_CODES = {0, 20, 30}  # 0: UNSAT, 20: SAT (one model), 30: all models

try:
    # Use sys.executable to ensure clingo runs from the current Python environment (e.g., virtual env)
    # Assumes clingo is installed via pip; runs as module: python -m clingo
    result = subprocess.run(
        [sys.executable, '-m', 'clingo', 'Generate_Roles.lp', 'state_space.lp', '--outf=1'],  # No --outf=1 for textual output
        capture_output=True,
        text=True,
        check=False  # Don't raise on non-zero
    )
    if result.returncode not in CLINGO_SUCCESS_CODES:
        print(f"Clingo failed with unexpected return code {result.returncode}. Stderr: {result.stderr}")
        exit(1)
    data = result.stdout
    print("Clingo output captured successfully.")

except FileNotFoundError:
    print("Error: Clingo module not found. Install via 'pip install clingo'.")
    exit(1)
except subprocess.CalledProcessError as e:
    # This shouldn't trigger with check=False, but handle any other subprocess issues
    print(f"Subprocess error: {e}")
    exit(1)

# Process data to extract only the ANSWER block (facts after 'ANSWER' until next '%' line)
lines = data.splitlines()
in_answer = False
answer_content = []
for line in lines:
    if line.strip() == "ANSWER":
        in_answer = True
        continue
    if in_answer and line.strip().startswith("%"):
        break
    if in_answer and line.strip():  # Skip empty lines within answer
        answer_content.append(line)

# Join the answer lines into a single string for parsing (facts are space-separated)
processed_data = ' '.join(answer_content)

print("Processed ANSWER block extracted.")

# Updated regex pattern to match textual output: holds("obj_id", ("relation", block1, block2), role).
# Assumes blocks are single lowercase letters [a-z], roles are words like 'star', 'plus', etc.
pattern = r'holds\("([^"]+)",\("([^"]+)",([a-z]),([a-z])\),([a-z]+)\)\.'

matches_found = 0
for match in re.finditer(pattern, processed_data):
    obj_id, relation, b1, b2, role = match.groups()
    new_relation = f"{relation}_{role}"  # Append role to relation
    print(f'holds("{obj_id}",("{new_relation}",{b1},{b2})).')
    matches_found += 1

if matches_found == 0:
    print("No matching 'holds' facts found in Clingo output.")
else:
    print(f"Extracted and transformed {matches_found} facts.")