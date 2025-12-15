clingo run.lp dl.lp "state_space" 1 | python asp2table.py > output.txt (for search)

clingo run.lp dl.lp experiments/instance_3_clear_x_2.lp --quiet=1 | python asp2table.py > output.txt  (for optimization) 

Experiments at: https://github.com/rleap-project/d2l/tree/main/domains




1) Generate Search Space:

`python ./Generate_ASP_State_Space.py /path/to/problem.pddl'

It assumes domain.pddl to be present in the same folder /path/to. Return /path/to/problem.lp', the logic program representing the search space.

2) Generate Roles

`