# SND-RR
An implementation of two dynamic discretization discovery (DDD) algorithms for solving the service network design problem with restricted routes. The two algorithms implemented are the arc-based and node-based DDD algorithms as described in the corresponding paper 
'Sparse dynamic discretization discovery via arc-dependent time discretizations'. The Arxiv version of this paper can be found 
[here]([https://www.example.com/paper](https://arxiv.org/abs/2305.19176)). This code was used for the comparison of runtime for two algorithms and the results
are reported in Section 7. For more details on the algorithms and their theoretical foundations please see the paper. 

### Running the code: 
The `Instances' folder includes the benchmarking instances considered. Additional instances in the same family
can be generated by assigning process = 'gen_instances', and specifying the family ('DP'->designated paths, 
'REGIONAL'->hub-and-spoke, 'GROUP_TIMES'->critical times) in the run_DDD() function in the main.py file. 

The instances are run by changing the process to 'run_instances', and again selected the family of instances to solve. 
Instances are stored in the instance folder, where there is a subfolder for each flat instance, and within each flat instance
folder there is set of SND instance folders. 


### Input: 
Each SND instance has the following input files:
- arcs.csv: row for each arc, column set ['origin', 'destination', 'transit_time', 'capacity', 'fixed_cost']
- commodities.csv: row for each commodity, column set ['origin', 'destination', 'demand', 'release_time', 'deadline', 'arc_list', 'node_list']
  (the latter two only used for designated path instances)
- nodes.csv: row for each node, column set ['id', 'hub', 'region_hub'] (the latter two only used for hub-and-spoke instances)
- parameters.csv: indicates instance family as well as the parameters used to generate the instance
- variable_costs.csv: the entry in row i, column j, gives the variable cost of commodity i on arc j

This code was used for the comparison of runtime for two algorithms and so the resulting solution is not produced. The 
solution can be obtained by printing the model solution for the final upper bound model solved, stored in self.LP_UB in 
the Instance_Solver.py file. 

### Output: 
- testing_summary.csv: includes total runtime, final solution cost, iteration count, and related algorithm characteristics. 


