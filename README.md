Problems for experiments at : https://github.com/rleap-project/d2l/tree/main/domains

1) Generate Search Space:

`python ./Generate_ASP_State_Space.py /path/to/problem.pddl'

It assumes domain.pddl to be present in the same folder /path/to. Return /path/to/problem.lp', the logic program representing the search space.

2) Generate Roles

`python ./Generate_Roles.py /path/to/problem.lp' 

It generate new roles (predicates) in file /path/to/problem-role.lp'

3) Compute Generalized Plan

`clingo run.lp dl.lp /path/to/problem.lp /path/to/problem-role.lp > python asp2table.py > output.txt