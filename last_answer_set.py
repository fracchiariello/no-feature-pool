#!/usr/bin/env python3
import sys

def main():
    last_answer = None
    expecting_atoms = False

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        if line.startswith("Answer"):
            expecting_atoms = True
            continue

        if expecting_atoms:
            last_answer = line
            expecting_atoms = False

    if last_answer is None:
        sys.exit(1)

    print(last_answer)

if __name__ == "__main__":
    main()
