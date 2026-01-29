#!/usr/bin/env python
# coding: utf-8

import os
import sys
import itertools
from collections import defaultdict, deque

from unified_planning.io import PDDLReader
from unified_planning.shortcuts import *


# -----------------------------
# Helpers
# -----------------------------

def fluent_to_tuple(fluent_exp):
    """
    Converts a Unified Planning fluent expression into an ASP-style tuple.

    Examples:
      ready        -> (ready)
      on(a,b)      -> (on, a, b)
      clear(x)     -> (clear, x)
    """
    name = fluent_exp.fluent().name
    args = [str(a.object()).lower() for a in fluent_exp.args]

    if not args:   # arity 0
        return f"({name},)"

    return f"({name}, {', '.join(args)})"


def upstate_to_asp(state, state_id, asp_states, problem):
    # Handle zero-arity fluents
    for fluent in problem.fluents:
        if fluent.arity == 0:
            fluent_exp = fluent()
            value = state.get_value(fluent_exp)
            if value.is_true():
                asp_states.append(
                    f"holds({state_id}, {fluent_to_tuple(fluent_exp)})."
                )
    
    # Handle grounded fluents with arity > 0
    # The state internally stores all true grounded fluents
    # We need to check all possible groundings
    for fluent in problem.fluents:
        if fluent.arity > 0:
            # Get all objects that could be arguments
            relevant_objects = []
            for param in fluent.signature:
                objects_of_type = problem.objects(param.type)
                relevant_objects.append(list(objects_of_type))
            
            # Generate all combinations
            import itertools
            for obj_combination in itertools.product(*relevant_objects):
                fluent_exp = fluent(*obj_combination)
                value = state.get_value(fluent_exp)
                if value.is_true():
                    asp_states.append(
                        f"holds({state_id}, {fluent_to_tuple(fluent_exp)})."
                    )


def get_state_id(problem_name, state):
    h = hash(state)
    return f"s_{problem_name}_{'p' if h >= 0 else 'm'}{abs(h)}"


def extract_objects_from_goal(problem):
    objs = set()

    def visit(expr: FNode):
        if expr.is_fluent_exp():
            for arg in expr.args:
                if arg.is_object_exp():
                    objs.add(arg.object())
        for sub in expr.args:
            if isinstance(sub, FNode):
                visit(sub)

    for goal in problem.goals:
        visit(goal)

    return objs


# -----------------------------
# Load problem
# -----------------------------

problem_file = sys.argv[1]
path = os.path.dirname(problem_file)
domain_file = os.path.join(path, "domain.pddl")
problem_name = os.path.splitext(os.path.basename(problem_file))[0]

reader = PDDLReader()
problem = reader.parse_problem(domain_file, problem_file)

goal_objects = extract_objects_from_goal(problem)

simulator = SequentialSimulator(problem=problem)
initial_state = simulator.get_initial_state()


# -----------------------------
# State space exploration
# -----------------------------

asp_states = []
asp_goal_states = []
asp_transitions = []

visited = set()
queue = [initial_state]
visited.add(initial_state)

forward_graph = defaultdict(list)
reverse_graph = defaultdict(list)

while queue:
    current = queue.pop(0)
    curr_id = get_state_id(problem_name, current)

    upstate_to_asp(current, curr_id, asp_states, problem)

    if simulator.is_goal(current):
        asp_goal_states.append(f"goal({curr_id}).")
        continue

    for act, params in simulator.get_applicable_actions(current):
        new_state = simulator.apply(current, act, params)
        new_id = get_state_id(problem_name, new_state)

        asp_transitions.append(f"transition({curr_id}, {new_id}).")

        forward_graph[curr_id].append(new_id)
        reverse_graph[new_id].append(curr_id)

        if new_state not in visited:
            visited.add(new_state)
            queue.append(new_state)


# -----------------------------
# Compute distance to goal
# -----------------------------

goal_ids = [g[len("goal("):-2] for g in asp_goal_states]

distance_to_goal = {}
queue = deque()

for gid in goal_ids:
    distance_to_goal[gid] = 0
    queue.append(gid)

while queue:
    current = queue.popleft()
    for pred in reverse_graph[current]:
        if pred not in distance_to_goal:
            distance_to_goal[pred] = distance_to_goal[current] + 1
            queue.append(pred)


# -----------------------------
# Write ASP output
# -----------------------------

max_distance = max(distance_to_goal.values()) if distance_to_goal else 0
output_file = os.path.join(path, f"{problem_name}.lp")

with open(output_file, "w") as f:
    for t in asp_transitions:
        f.write(t + "\n")

    for s in asp_states:
        f.write(s + "\n")

    f.write(f"init({get_state_id(problem_name, initial_state)}).\n")

    for g in asp_goal_states:
        f.write(g + "\n")

    for obj in goal_objects:
        f.write(f"goal_object({str(obj).lower()}).\n")

    for sid, dist in distance_to_goal.items():
        f.write(f"v_star({sid}, {dist}).\n")

    f.write(f"max_v_star({max_distance}).\n")

print(f"ASP states, transitions, and distances saved to {output_file}")