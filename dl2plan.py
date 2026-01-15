import dlplan

domain = 'domains/blocks_clear/domain.pddl'
problem = 'domains/blocks_clear/instance_5_clear_x.pddl'
state_space = generate_state_space(domain, problem).state_space