#!/usr/bin/env python3
"""
asp2table.py  (ATOM-BASED — no quotation marks)

Reads Clingo/ASP output from stdin and prints:

0) Raw input
1) Concept rules per time step + Selected + Feature Type
2) Concept objects per state (LAST Answer only)
3) Values table (LAST Answer only)
4) Evaluations table (LAST Answer only)
5) Good transitions + delta vectors (LAST Answer only)
"""

import sys
import re
from collections import defaultdict

CELL_WIDTH = 34
SEPARATOR = " | "

# -----------------------------
# Formatting helpers
# -----------------------------
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
# Read raw Clingo output
# -----------------------------
SOURCE = sys.stdin.read()
print(SOURCE)

# =====================================================
# FIRST TABLE — rule selections
# =====================================================

rule_pattern = re.compile(
    r'selectRule\(\s*(\d+)\s*,\s*([^,]+)\s*,\s*([A-Za-z_]+)\s*\)'
)

rules = rule_pattern.findall(SOURCE)

selectRule = defaultdict(dict)
times_seen = set()
concepts_seen = set()

for t_s, concept, rule in rules:
    t = int(t_s)
    selectRule[concept][t] = rule
    times_seen.add(t)
    concepts_seen.add(concept)

selected = set(re.findall(r'select\(\s*([^)]+)\s*\)', SOURCE))
bool_features = set(re.findall(r'boolean_feature\(\s*([^)]+)\s*\)', SOURCE))
num_features = set(re.findall(r'numerical_feature\(\s*([^)]+)\s*\)', SOURCE))

param_pattern = re.compile(
    r'param\(\s*(\d+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)'
)
param = {(int(t), c): v for t, c, v in param_pattern.findall(SOURCE)}

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
        if t in selectRule[c]:
            rule = selectRule[c][t]
            p = fetch_param(t, c, rule)
            row.append(rule if p is None else f"{rule} : {p}")
        else:
            row.append("")
    row.append("yes" if c in selected else "no")
    if c in bool_features:
        row.append("boolean")
    elif c in num_features:
        row.append("numerical")
    else:
        row.append("")
    rows1.append(row)

# =====================================================
# SECOND TABLE — concept objects per state
# =====================================================

concept_re = re.compile(
    r'concept\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*\d+\s*\)'
)

state_features = defaultdict(lambda: defaultdict(set))
states_seen = set()
features_seen = set()

for feat, state, obj in concept_re.findall(SOURCE):
    state_features[state][feat].add(obj)
    states_seen.add(state)
    features_seen.add(feat)

ordered_states = sorted(states_seen)

header2 = ["Feature"] + ordered_states
rows2 = [header2]

for f in sorted(features_seen):
    row = [f]
    for s in ordered_states:
        objs = state_features[s].get(f, set())
        row.append(", ".join(sorted(objs)) if objs else "")
    rows2.append(row)

# =====================================================
# THIRD TABLE — values
# =====================================================

value_re = re.compile(
    r'value\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*(-?\d+)\s*\)'
)

value_map = defaultdict(dict)
value_features = set()

for feat, state, v in value_re.findall(SOURCE):
    value_map[state][feat] = int(v)
    value_features.add(feat)

states_seen |= set(value_map.keys())
ordered_states = sorted(states_seen)

header3 = ["Feature"] + ordered_states
rows3 = [header3]

for f in sorted(value_features):
    row = [f]
    for s in ordered_states:
        row.append(value_map[s].get(f, ""))
    rows3.append(row)

# =====================================================
# FOURTH TABLE — evaluations
# =====================================================

eval_re = re.compile(
    r'evaluation\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*(-?\d+)\s*\)'
)

eval_map = defaultdict(dict)
eval_features = set()

for feat, state, v in eval_re.findall(SOURCE):
    eval_map[state][feat] = int(v)
    eval_features.add(feat)

states_seen |= set(eval_map.keys())
ordered_states = sorted(states_seen)

header4 = ["Feature"] + ordered_states
rows4 = [header4]

for f in sorted(eval_features):
    row = [f]
    for s in ordered_states:
        row.append(eval_map[s].get(f, ""))
    rows4.append(row)

# =====================================================
# DELTA vectors
# =====================================================

delta_re = re.compile(
    r'delta\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)'
)

delta_map = defaultdict(dict)

for s1, s2, c, d in delta_re.findall(SOURCE):
    delta_map[(s1, s2)][c] = d

# =====================================================
# PRINT TABLES
# =====================================================

print_table("FIRST TABLE", rows1)
print_table("SECOND TABLE (concept objects per state)", rows2)
print_table("THIRD TABLE (values)", rows3)
print_table("FOURTH TABLE (evaluations)", rows4)

# =====================================================
# GOOD TRANSITIONS
# =====================================================

good_re = re.compile(r'good\(\s*([^,]+)\s*,\s*([^)]+)\s*\)')
good_edges = good_re.findall(SOURCE)

selected_concepts = sorted(selected)

print("\nGOOD TRANSITIONS:")

for s1, s2 in good_edges:
    v1 = [value_map[s1].get(c, "?") for c in selected_concepts]
    v2 = [value_map[s2].get(c, "?") for c in selected_concepts]
    e1 = [eval_map[s1].get(c, "?") for c in selected_concepts]
    e2 = [eval_map[s2].get(c, "?") for c in selected_concepts]
    d  = [delta_map.get((s1, s2), {}).get(c, "?") for c in selected_concepts]

    print(f"\nTransition: {s1} -> {s2}")
    print(f"Value:       {v1} -> {v2}")
    print(f"Evaluation:  {e1} -> {e2}")
    print(f"Delta:       {d}")
