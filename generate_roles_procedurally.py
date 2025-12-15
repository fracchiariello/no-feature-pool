import re
from collections import defaultdict
from itertools import combinations_with_replacement

def compose(rel1, rel2):
    composed = set()
    for x, y in rel1:
        for y2, z in rel2:
            if y == y2:
                composed.add((x, z))
    return composed

def transitive_closure(rel):
    reachable = set(rel)
    changed = True
    while changed:
        changed = False
        new_pairs = set()
        for x, y in list(reachable):
            for y_next, z in rel:
                if y == y_next and (x, z) not in reachable:
                    new_pairs.add((x, z))
                    changed = True
        reachable.update(new_pairs)
    return reachable

def compute_set(name, state_rels, definitions, memo):
    if name in memo:
        return memo[name]
    op, arg1, arg2 = definitions[name]
    if op == 'primitive':
        s = state_rels.get(name, set())
    elif op == 'inter':
        s1 = compute_set(arg1, state_rels, definitions, memo)
        s2 = compute_set(arg2, state_rels, definitions, memo)
        s = s1 & s2
    elif op == 'compose':
        s1 = compute_set(arg1, state_rels, definitions, memo)
        s2 = compute_set(arg2, state_rels, definitions, memo)
        s = compose(s1, s2)
    elif op == 'tc':
        s1 = compute_set(arg1, state_rels, definitions, memo)
        s = transitive_closure(s1)
    memo[name] = s
    return s

# Read the file
with open('state_space.lp', 'r') as f:
    content = f.read()

# Parse holds by state
state_to_rels = defaultdict(lambda: defaultdict(set))
states = set()
binary_preds = set()
for line in content.splitlines():
    if line.strip().startswith('holds('):
        # Match binary: holds("state", ("pred", arg1, arg2)).
        match = re.match(r'holds\("([^"]+)",\s*\(\s*"([^"]+)",\s*([a-z]+),\s*([a-z]+)\s*\)\)\s*\.', line)
        if match:
            state, pred, x, y = match.groups()
            state_to_rels[state][pred].add((x, y))
            states.add(state)
            binary_preds.add(pred)

print("States found:", sorted(states))
print("Binary predicates:", sorted(binary_preds))
print()

# Compute union rels for generation
union_rels = {pred: set.union(*(state_to_rels[state].get(pred, set()) for state in states)) for pred in binary_preds}

# Generate definitions on union
name_to_set = dict(union_rels)
set_to_name = {frozenset(rel_set): pred for pred, rel_set in union_rels.items()}
definitions = {pred: ('primitive', None, None) for pred in binary_preds}

rel_counter = 1
changed = True
while changed:
    changed = False
    new_items = []
    names = sorted(name_to_set.keys())  # Sort for reproducibility
    # Intersections
    for i in range(len(names)):
        for j in range(i, len(names)):
            p1 = names[i]
            p2 = names[j]
            inter_set = name_to_set[p1] & name_to_set[p2]
            if inter_set:
                fs = frozenset(inter_set)
                if fs not in set_to_name:
                    prop_name = f"{p1}_inter_{p2}" if p1 != p2 else f"{p1}_self_inter"
                    new_items.append((fs, prop_name, 'inter', p1, p2))
    # Compositions
    for p1 in names:
        for p2 in names:
            comp_set = compose(name_to_set[p1], name_to_set[p2])
            if comp_set:
                fs = frozenset(comp_set)
                if fs not in set_to_name:
                    prop_name = f"{p1}_compose_{p2}"
                    new_items.append((fs, prop_name, 'compose', p1, p2))
    # Transitive closures
    for p in names:
        tc_set = transitive_closure(name_to_set[p])
        if tc_set:
            fs = frozenset(tc_set)
            if fs not in set_to_name:
                prop_name = f"{p}_tc"
                new_items.append((fs, prop_name, 'tc', p, None))
    # Add new
    for fs, prop_name, op, arg1, arg2 in new_items:
        name = prop_name
        while name in name_to_set:
            name = f"{prop_name}_{rel_counter}"
            rel_counter += 1
        name_to_set[name] = set(fs)
        set_to_name[fs] = name
        definitions[name] = (op, arg1, arg2)
        changed = True

all_derived_names = sorted(definitions.keys())
print(f"Generated {len(all_derived_names)} derived predicate names.")
print()

# Now for each state, compute and output
for state in sorted(states):
    print(f"% Derived relations for state: {state}")
    state_rels = state_to_rels[state]
    memo = {}
    for name in all_derived_names:
        s = compute_set(name, state_rels, definitions, memo)
        if s:  # Only output if non-empty
            print(f"% {name}")
            for x, y in sorted(s):
                print(f'holds("{state}", ("{name}", {x}, {y})).')
    print()