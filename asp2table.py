#!/usr/bin/env python3
"""
asp2table.py

Reads Clingo/ASP output from stdin and prints two tables:

1) First table: concept rules per time step + Selected + Feature Type
   - Parses selectRule/3, param/3, paramR/3, paramN/3, select/1,
     boolean_feature/1, numerical_feature/1

2) Second table: features x states (ordered from initial -> goal by good/2)
   - Uses only concept(feature, state, object, t) facts with t == LAST_T
   - Lists the exact objects (unique) for each (feature,state) at LAST_T

Assumptions:
- No duplicate identical concept facts for the same (feature,state,obj,time)
- good/2 forms a chain; fallback to best-effort if not exactly a single chain.
"""

import sys
import re
from collections import defaultdict

# -----------------------------
# Configuration
# -----------------------------
CELL_WIDTH = 34    # adjust if you want wider/narrower columns
SEPARATOR = " | "

# -----------------------------
# Helpers
# -----------------------------
def clean_token(tok: str) -> str:
    """Strip whitespace and surrounding quotes from a token."""
    tok = tok.strip()
    if tok.startswith('"') and tok.endswith('"') and len(tok) >= 2:
        return tok[1:-1]
    return tok

def fmt_row(row, widths):
    return SEPARATOR.join(str(col).ljust(w) for col, w in zip(row, widths))

def compute_col_widths(rows, min_width=CELL_WIDTH):
    """Compute column widths from rows (list of lists)."""
    if not rows:
        return []
    ncols = len(rows[0])
    widths = [min_width] * ncols
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(str(cell)) + 1)
    return widths

# -----------------------------
# Read input
# -----------------------------
data = sys.stdin.read()
print(data)

# -----------------------------
# Parse first-table related facts
# -----------------------------

# selectRule(time,"concept",rule)
rule_pattern = re.compile(r'selectRule\(\s*([0-9]+)\s*,\s*"([^"]+)"\s*,\s*([A-Za-z_]+)\s*\)')
rules = rule_pattern.findall(data)

selectRule = defaultdict(dict)  # concept -> time -> rule
times_seen = set()
concepts_seen = set()

for t_s, c_s, rule in rules:
    t = int(t_s)
    c = clean_token(c_s)
    selectRule[c][t] = rule
    times_seen.add(t)
    concepts_seen.add(c)

# select("concept")
selected_pattern = re.compile(r'select\(\s*"([^"]+)"\s*\)')
selected = {clean_token(s) for s in selected_pattern.findall(data)}

# boolean_feature("f") and numerical_feature("f")
bool_pattern = re.compile(r'boolean_feature\(\s*"([^"]+)"\s*\)')
num_pattern = re.compile(r'numerical_feature\(\s*"([^"]+)"\s*\)')
bool_features = {clean_token(s) for s in bool_pattern.findall(data)}
numerical_features = {clean_token(s) for s in num_pattern.findall(data)}

# params: param(time,"concept","val") paramR(...) paramN(...)
param_pattern  = re.compile(r'param\(\s*([0-9]+)\s*,\s*"([^"]+)"\s*,\s*"?(.*?)"?\s*\)')
paramR_pattern = re.compile(r'paramR\(\s*([0-9]+)\s*,\s*"([^"]+)"\s*,\s*"?(.*?)"?\s*\)')
paramN_pattern = re.compile(r'paramN\(\s*([0-9]+)\s*,\s*"([^"]+)"\s*,\s*(.*?)\s*\)')

param  = {(int(t), clean_token(c)): v for t, c, v in param_pattern.findall(data)}
paramR = {(int(t), clean_token(c)): v for t, c, v in paramR_pattern.findall(data)}
paramN = {(int(t), clean_token(c)): v for t, c, v in paramN_pattern.findall(data)}

no_param_rules = {"negation", "top", "bottom"}

def fetch_param(t, c, rule):
    """Return parameter string or None if rule has no parameter."""
    if rule in no_param_rules:
        return None
    if rule in ("conjunction", "disjunction"):
        return param.get((t, c))
    if rule in ("forall", "exists"):
        return paramR.get((t, c))
    return paramN.get((t, c))

# -----------------------------
# Parse concept facts for second table
# -----------------------------
# concept("feature","state", OBJECT, time)
# OBJECT may be quoted "..." or an unquoted token (alphanumeric + underscore)
concept_re = re.compile(
    r'concept\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(".*?"|[A-Za-z0-9_]+)\s*,\s*([0-9]+)\s*\)'
)
concept_facts = concept_re.findall(data)

# Determine LAST_T (max time across all concept facts)
all_times = [int(t_s) for *_, t_s in concept_facts]
LAST_T = max(all_times) if all_times else None

# Build mapping state -> feature -> set(objects) but only for t == LAST_T
state_features = defaultdict(lambda: defaultdict(set))
states_seen = set()
features_seen = set()

if LAST_T is not None:
    for feat, state, obj_tok, t_s in concept_facts:
        t = int(t_s)
        if t != LAST_T:
            continue
        feat_c = clean_token(feat)
        state_c = clean_token(state)
        obj_c = clean_token(obj_tok)
        state_features[state_c][feat_c].add(obj_c)
        states_seen.add(state_c)
        features_seen.add(feat_c)

# -----------------------------
# Parse good/2 edges to build ordered states chain
# -----------------------------
good_re = re.compile(r'good\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)')
edges = good_re.findall(data)

successor = {}
predecessor = set()
all_states_from_edges = set()

for a_raw, b_raw in edges:
    a = clean_token(a_raw)
    b = clean_token(b_raw)
    successor[a] = b
    predecessor.add(b)
    all_states_from_edges.add(a)
    all_states_from_edges.add(b)

# Determine initial state (not appearing as second arg)
initial_states = [s for s in all_states_from_edges if s not in predecessor]

if len(initial_states) == 1:
    initial_state = initial_states[0]
    # build ordered chain
    ordered_states = [initial_state]
    while ordered_states[-1] in successor:
        ordered_states.append(successor[ordered_states[-1]])
else:
    # fallback: if good/2 chain is missing or ambiguous, try to order using states_seen
    # prefer states appearing in edges first (in sorted order), then remaining states
    if all_states_from_edges:
        # attempt to assemble best-effort chain:
        # find nodes with no predecessor (could be more than one) and walk each
        starts = [s for s in all_states_from_edges if s not in predecessor]
        starts_sorted = sorted(starts) if starts else sorted(all_states_from_edges)
        chain = []
        visited = set()
        for st in starts_sorted:
            cur = st
            while cur and cur not in visited:
                chain.append(cur)
                visited.add(cur)
                cur = successor.get(cur)
        # append any leftover states
        leftover = sorted(all_states_from_edges - set(chain))
        ordered_states = chain + leftover
    else:
        # last fallback: use states discovered in concepts at LAST_T (sorted)
        ordered_states = sorted(states_seen)

# -----------------------------
# Build First Table rows
# -----------------------------
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
# Build Second Table rows (objects listed for LAST_T)
# -----------------------------
header2 = ["Feature"] + ordered_states
rows2 = [header2]
features_sorted = sorted(features_seen)

for f in features_sorted:
    row = [f]
    for s in ordered_states:
        objs = state_features.get(s, {}).get(f, set())
        if objs:
            # sort object names for reproducible order
            cell = ", ".join(sorted(objs))
        else:
            cell = ""
        row.append(cell)
    rows2.append(row)

# -----------------------------
# Print both tables with computed widths
# -----------------------------
# Compute column widths from both tables to keep formatting reasonable
widths1 = compute_col_widths(rows1, min_width=CELL_WIDTH)
widths2 = compute_col_widths(rows2, min_width=CELL_WIDTH)

# Print first table
print("\nFIRST TABLE:")
print(fmt_row(rows1[0], widths1))
print("-" * (sum(widths1) + len(SEPARATOR) * (len(widths1) - 1)))
for r in rows1[1:]:
    print(fmt_row(r, widths1))

# Print second table
print("\nSECOND TABLE (objects at last time t={}):".format(LAST_T if LAST_T is not None else "N/A"))
print(fmt_row(rows2[0], widths2))
print("-" * (sum(widths2) + len(SEPARATOR) * (len(widths2) - 1)))
for r in rows2[1:]:
    print(fmt_row(r, widths2))

# -----------------------------
# Parse evaluation(feature,state,value) for THIRD TABLE
# -----------------------------
eval_re = re.compile(
    r'evaluation\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([0-9]+)\s*\)'
)
eval_facts = eval_re.findall(data)

# Build dictionary: eval_map[state][feature] = value
eval_map = defaultdict(dict)
eval_features = set()
eval_states = set()

for feat, state, val_s in eval_facts:
    f = clean_token(feat)
    s = clean_token(state)
    v = int(val_s)
    eval_map[s][f] = v
    eval_features.add(f)
    eval_states.add(s)

# Restrict to SELECTED FEATURES only (your requirement)
selected_eval_features = sorted([f for f in eval_features if f in selected])

# Build Third Table
header3 = ["Feature"] + ordered_states
rows3 = [header3]

for f in selected_eval_features:
    row = [f]
    for st in ordered_states:
        cell = eval_map.get(st, {}).get(f, "")
        row.append(cell)
    rows3.append(row)

# Compute widths
widths3 = compute_col_widths(rows3, min_width=CELL_WIDTH)

# Print third table
print("\nTHIRD TABLE (boolean evaluations):")
print(fmt_row(rows3[0], widths3))
print("-" * (sum(widths3) + len(SEPARATOR) * (len(widths3) - 1)))
for r in rows3[1:]:
    print(fmt_row(r, widths3))

