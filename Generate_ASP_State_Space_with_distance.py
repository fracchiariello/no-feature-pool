#!/usr/bin/env python
# coding: utf-8

import re
import os
import sys
from collections import defaultdict, deque

from unified_planning.io import PDDLReader
from unified_planning.shortcuts import *

def predicate_to_tuple(atom):
    predicate, args = atom.rstrip(')').split('(')
    arg_list = [arg.strip() for arg in args.split(',')]
    return f'("{predicate}", {", ".join(arg_list)})'


def upstate_to_asp(state, state_id, asp_states):
    s = str(state)
    pattern = r'([a-zA-Z0-9_-]*\([^)]+\)): (true|false)'
    matches = re.findall(pattern, s)
    for predicate, value in matches:
        if value == 'true':
            asp_states.append(f"holds({state_id}, {predicate_to_tuple(predicate)}).")


def get_state_id(problem_name, state):
    state_hash = state.__hash__()
    if state_hash >= 0:
        state_id = f"s_{problem_name}_p{state_hash}"
    else:
        state_id = f"s_{problem_name}_m{abs(state_hash)}"
    return '"' + state_id + '"'


# ------------------------------------------------------------------
# Load problem
# ------------------------------------------------------------------

problem_file = sys.argv[1]
path = os.path.dirname(problem_file)
domain_file = os.path.join(path, "domain.pddl")
problem_name = os.path.splitext(os.path.basename(problem_file))[0]

reader = PDDLReader()
problem = reader.parse_problem(domain_file, problem_file)

simulator = SequentialSimulator(problem=problem)
initial_state = simulator.get_initial_state()

# ------------------------------------------------------------------
# State-space exploration
# ------------------------------------------------------------------

asp_states = []
asp_goal_states = []
asp_transitions = []

visited = set()
queue = [initial_state]
visited.add(initial_state)

# Graphs for distance computation
forward_graph = defaultdict(list)
reverse_graph = defaultdict(list)

while queue:
    current = queue.pop(0)
    curr_id = get_state_id(problem_name, current)

    upstate_to_asp(current, curr_id, asp_states)

    if simulator.is_goal(current):
        asp_goal_states.append(f"goal({curr_id}).")
    else:
        for act in simulator.get_applicable_actions(current):
            new_state = simulator.apply(current, act[0], act[1])
            new_id = get_state_id(problem_name, new_state)

            asp_transitions.append(f"transition({curr_id}, {new_id}).")
            forward_graph[curr_id].append(new_id)
            reverse_graph[new_id].append(curr_id)

            if new_state not in visited:
                visited.add(new_state)
                queue.append(new_state)

# ------------------------------------------------------------------
# Compute optimal distance to goal (reverse BFS)
# ------------------------------------------------------------------

goal_ids = [line[len("goal("):-2] for line in asp_goal_states]

distance_to_goal = {}
queue = deque()

for gid in goal_ids:
    distance_to_goal[gid] = 0
    queue.append(gid)

while queue:
    current = queue.popleft()
    for predecessor in reverse_graph[current]:
        if predecessor not in distance_to_goal:
            distance_to_goal[predecessor] = distance_to_goal[current] + 1
            queue.append(predecessor)

# ------------------------------------------------------------------
# Write ASP output
# ------------------------------------------------------------------

output_file = os.path.join(path, f"{problem_name}.lp")
with open(output_file, 'w') as f:
    for transition in asp_transitions:
        f.write(transition + '\n')

    for state_fluent in asp_states:
        f.write(state_fluent + '\n')

    f.write(f"init({get_state_id(problem_name, initial_state)}).\n")

    for goal_state in asp_goal_states:
        f.write(goal_state + '\n')

    for state_id, dist in distance_to_goal.items():
        f.write(f"v_star({state_id}, {dist}).\n")

print(f"ASP states, transitions, and distances saved to {output_file}")
