import subprocess
import re
import sys  # Add this import for sys.executable

# Define success codes for Clingo (adjust based on your needs)
CLINGO_SUCCESS_CODES = {0, 20, 30}  # 0: UNSAT, 20: SAT (one model), 30: all models

try:
    # Use sys.executable to ensure clingo runs from the current Python environment (e.g., virtual env)
    # Assumes clingo is installed via pip; runs as module: python -m clingo
    # Get input file from command line argument
    if len(sys.argv) < 2:
        print("Usage: python Generate_Roles.py <input_file>")
        exit(1)
    
    input_file = sys.argv[1]

    result = subprocess.run(
        [sys.executable, '-m', 'clingo', 'Generate_Roles.lp', input_file, '--outf=1'],
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
# Allows alphanumeric characters for blocks and roles
pattern = r'holds\("([^"]+)",\("([^"]+)",([a-zA-Z0-9]+),([a-zA-Z0-9]+)\),([a-zA-Z0-9]+)\)\.'

matches_found = 0
output_file = None
try:
    for match in re.finditer(pattern, processed_data):
        obj_id, relation, b1, b2, role = match.groups()
        new_relation = f"{relation}_{role}"  # Append role to relation
        if matches_found == 0:
            # Open file for writing on first match
            output_filename = input_file.rsplit('.', 1)[0] + '-role.' + input_file.rsplit('.', 1)[1]
            output_file = open(output_filename, 'w')
        output_file.write(f'holds("{obj_id}",("{new_relation}",{b1},{b2})).\n')
        matches_found += 1
finally:
    if output_file:
        output_file.close()

if matches_found == 0:
    print("No matching 'holds' facts found in Clingo output.")
else:
    print(f"Extracted and transformed {matches_found} facts.")