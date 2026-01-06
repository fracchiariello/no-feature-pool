#!/usr/bin/env python3
"""
asp2table.py

Reads Clingo/ASP output from stdin and prints:

0) The raw input
1) Concept rules per time step + Selected + Feature Type
2) Features x States (objects at LAST_T from concept/4)
3) Values table from value(C,S,N)
4) Evaluations table from evaluation(C,S,V)
"""

import sys
import re
from collections import defaultdict

# -----------------------------
# Configuration
# -----------------------------
CELL_WIDTH = 34
SEPARATOR = " | "

# -----------------------------
# Helpers
# -----------------------------
def clean_token(tok: str) -> str:
    tok = tok.strip()
    if tok.startswith('"') and tok.endswith('"') and len(tok) >= 2:
        return tok[1:-1]
    return tok

def fmt_row(row, widths):
    return SEPARATOR.join(str(col).ljust(w) for col, w in zip(row, widths))

def compute_col_widths(rows, min_width=CELL_WIDTH):
    if not rows:
        return []
    ncols = len(rows[0])
    widths = [min_width] * ncols
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(str(cell)) + 1)
    return widths

def print_table(title, rows):
    widths = compute_col_widths(rows)
    print(f"\n{title}:")
    print(fmt_row(rows[0], widths))
    print("-" * (sum(widths) + len(SEPARATOR) * (len(widths) - 1)))
    for r in rows[1:]:
        print(fmt_row(r, widths))

# -----------------------------
# Read & print input
# -----------------------------
data = sys.stdin.read()
print(data)

# -----------------------------
# FIRST TABLE: rules
# -----------------------------
rule_pattern = re.compile(
    r'selectRule\(\s*([0-9]+)\s*,\s*"([^"]+)"\s*,\s*([A-Za-z_]+)\s*\)'
)
rules = rule_pattern.findall(data)

selectRule = defaultdict(dict)
times_seen = set()
concepts_seen = set()

for t_s, c_s, rule in rules:
    t = int(t_s)
    c = clean_token(c_s)
    selectRule[c][t] = rule
    times_seen.add(t)
    concepts_seen.add(c)

selected_pattern = re.compile(r'select\(\s*"([^"]+)"\s*\)')
selected = {clean_token(s) for s in selected_pattern.findall(data)}

bool_pattern = re.compile(r'boolean_feature\(\s*"([^"]+)"\s*\)')
num_pattern = re.compile(r'numerical_feature\(\s*"([^"]+)"\s*\)')
bool_features = {clean_token(s) for s in bool_pattern.findall(data)}
numerical_features = {clean_token(s) for s in num_pattern.findall(data)}

param_pattern = re.compile(
    r'param\(\s*([0-9]+)\s*,\s*"([^"]+)"\s*,\s*"?(.*?)"?\s*\)'
)
param = {(int(t), clean_token(c)): v for t, c, v in param_pattern.findall(data)}

no_param_rules = {"negation", "top", "bottom", "copy"}

def fetch_param(t, c, rule):
    if rule in no_param_rules:
        return None
    return param.get((t, c))

times_sorted = sorted(times_seen)
concepts_sorted = sorted(concepts_seen)

header1 = ["Concept"] + [f"t={t}" for t in times_sorted] + ["Selected", "Feature Type"]
rows1 = [header1]

for c in concepts_sorted:
    row = [c]
    for t in times_sorted:
        if t in selectRule.get(c, {}):
            rule = selectRule[c][t]
            p = fetch_param(t, c, rule)
            cell = rule if p is None else f"{rule} : {p}"
        else:
            cell = ""
        row.append(cell)
    row.append("yes" if c in selected else "no")
    if c in bool_features:
        row.append("boolean")
    elif c in numerical_features:
        row.append("numerical")
    else:
        row.append("")
    rows1.append(row)

# -----------------------------
# SECOND TABLE: concept objects at LAST_T
# -----------------------------
concept_re = re.compile(
    r'concept\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(".*?"|[A-Za-z0-9_]+)\s*,\s*([0-9]+)\s*\)'
)
concept_facts = concept_re.findall(data)

all_times = [int(t_s) for *_, t_s in concept_facts]
LAST_T = max(all_times) if all_times else None

state_features = defaultdict(lambda: defaultdict(set))
states_seen = set()
features_seen = set()

if LAST_T is not None:
    for feat, state, obj_tok, t_s in concept_facts:
        if int(t_s) != LAST_T:
            continue
        f = clean_token(feat)
        s = clean_token(state)
        o = clean_token(obj_tok)
        state_features[s][f].add(o)
        states_seen.add(s)
        features_seen.add(f)

ordered_states = sorted(states_seen)

header2 = ["Feature"] + ordered_states
rows2 = [header2]

for f in sorted(features_seen):
    row = [f]
    for s in ordered_states:
        objs = state_features.get(s, {}).get(f, set())
        row.append(", ".join(sorted(objs)) if objs else "")
    rows2.append(row)

# -----------------------------
# THIRD TABLE: value(C,S,N)
# -----------------------------
value_re = re.compile(
    r'value\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([0-9]+)\s*\)'
)
value_facts = value_re.findall(data)

value_map = defaultdict(dict)
value_features = set()

for feat, state, n_s in value_facts:
    f = clean_token(feat)
    s = clean_token(state)
    value_map[s][f] = int(n_s)
    value_features.add(f)

header3 = ["Feature"] + ordered_states
rows3 = [header3]

for f in sorted(value_features):
    row = [f]
    for s in ordered_states:
        row.append(value_map.get(s, {}).get(f, ""))
    rows3.append(row)

# -----------------------------
# FOURTH TABLE: evaluation(C,S,V)
# -----------------------------
eval_re = re.compile(
    r'evaluation\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([0-9]+)\s*\)'
)
eval_facts = eval_re.findall(data)

eval_map = defaultdict(dict)
eval_features = set()

for feat, state, v_s in eval_facts:
    f = clean_token(feat)
    s = clean_token(state)
    eval_map[s][f] = int(v_s)
    eval_features.add(f)

header4 = ["Feature"] + ordered_states
rows4 = [header4]

for f in sorted(eval_features):
    row = [f]
    for s in ordered_states:
        row.append(eval_map.get(s, {}).get(f, ""))
    rows4.append(row)

# -----------------------------
# Print tables
# -----------------------------
print_table("FIRST TABLE", rows1)
print_table(f"SECOND TABLE (objects at last time t={LAST_T})", rows2)
print_table("THIRD TABLE (values)", rows3)
print_table("FOURTH TABLE (evaluations)", rows4)
