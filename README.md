clingo run.lp dl.lp "state_space" 1 | python asp2table.py > output.txt (for search)

clingo run.lp dl.lp experiments/instance_3_clear_x_2.lp --quiet=1 | python asp2table.py > output.txt  (for optimization) 