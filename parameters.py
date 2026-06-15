## Simulation parameters
N = 100 # Number of graph nodes
family_size = 5 # it must divide N
affinity_step = 20
alpha = 0.1 # exponential decrease for indirect connections
l_max = 5 # max number of intermediates nodes for reputational flow
max_time = 15
nbr_size = 2 # number of characters needed to write the time
cost = 0.12
beta = -1
rep_flow_weights = [0, 0.25, 0.5, 0.75, 1]

## Simulation parameters & plot average
nbr_simus = 5 # for each rep_flow_weight
nbr_simu_size = 2 # number of characters needed to write the number of simulations
nbr_weight_size = 3