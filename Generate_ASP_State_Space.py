#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#get_ipython().run_line_magic('pip', 'install unified-planning[fast-downward] --quiet')


# In[1]:


import re
import os

def predicate_to_tuple(atom):
    # Remove the closing parenthesis and split by the opening parenthesis
    predicate, args = atom.rstrip(')').split('(')
    # Split the arguments by comma and strip whitespace
    arg_list = [arg.strip() for arg in args.split(',')]
    # Create the tuple with quoted predicate and unquoted arguments
    result = f'("{predicate}", {", ".join(arg_list)})'
    return result


def upstate_to_asp(state, state_id, asp_states):
    s = str(state)
    pattern = r'([a-zA-Z0-9_-]*\([^)]+\)): (true|false)'
    matches = re.findall(pattern, s)
    for predicate, value in matches:
        if value == 'true':
            asp_states.append(f"holds({state_id}, {predicate_to_tuple(predicate)}).")


# In[2]:

import sys
from unified_planning.io import PDDLReader

problem_file = sys.argv[1]
path = os.path.dirname(problem_file)
domain_file = os.path.join(path, "domain.pddl")
problem_name = os.path.splitext(os.path.basename(problem_file))[0]


reader = PDDLReader()
problem = reader.parse_problem(domain_file, problem_file)


# In[3]:


from unified_planning.shortcuts import *

simulator = SequentialSimulator(problem=problem)
initial_state = simulator.get_initial_state()


# In[4]:


asp_states = []
asp_goal_states = []

# BFS to visit all reachable states using list as queue
visited = set()
queue = [initial_state]
visited.add(initial_state)


asp_transitions = []

def get_state_id(problem_name,state):
    state_hash = state.__hash__()
    if state_hash >= 0:
        state_id = f"s_{problem_name}_p{state_hash}"
    else:
        state_id = f"s_{problem_name}_m{abs(state_hash)}" #adding the sign to the state id as a m (for minus) as clingo does not support signs in the names
    return '"'+state_id+'"'

while queue:
    current = queue.pop(0)
    curr_id = get_state_id(problem_name,current)
    upstate_to_asp(current, curr_id, asp_states)
    if simulator.is_goal(current):
        asp_goal_states.append(f"goal({curr_id}).")
    else: 
        for act in simulator.get_applicable_actions(current):
            new_state = simulator.apply(current, act[0], act[1])
            new_id = get_state_id(problem_name,new_state)
            asp_transitions.append(f"transition({curr_id}, {new_id}).")
            if new_state not in visited:
                visited.add(new_state)
                queue.append(new_state)


# In[5]:


output_file = os.path.join(path, f"{problem_name}.lp")
with open(output_file, 'w') as f:
    for transition in asp_transitions:
        f.write(transition + '\n')
    for state_fluent in asp_states:
        f.write(state_fluent + '\n')
    f.write(f"init({get_state_id(problem_name,initial_state)}). \n")
    for goal_state in asp_goal_states:
        f.write(goal_state + '\n')

print(f"ASP states and transitions saved to {output_file}")


# In[ ]:




