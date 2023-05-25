import gurobipy as gp
from gurobipy import GRB
import time
import networkx as nx


class SNDSolver:
    def __init__(self, Input_data, G_S, D_S, time_limit):
        time1 = time.time()
        self.K = Input_data.K
        self.V_S = G_S.V_S
        self.E_S = G_S.E_S
        self.F_S = G_S.F_S
        self.A_S = D_S.A_S

        self.model = gp.Model('SND_IP')
        self.model.Params.OutputFlag = 0
        self.model.Params.MIPgap = 0.01
        self.model.Params.TimeLimit = time_limit
        self.constraints = []
        self.vars = []
        self.status = 'status'
        self.mip_gap = 100
        self.obj_val = 0

        self.solve_network()
        self.num_constraints = sum(self.constraints)
        self.num_vars = sum(self.vars)
        if self.model.status == GRB.INFEASIBLE:
            quit('Lower bound formulation was not feasible.')
        if self.model.status != GRB.INFEASIBLE:
            self.obj_val = self.model.ObjBound
            self.mip_gap = self.model.MIPGap
        if self.model.status == GRB.OPTIMAL:
            self.obj_val = self.model.ObjBound
        self.solution_time = round(time.time() - time1, 2)
        print('solution time:', self.solution_time)

    def solve_network(self):
        self.__add_variables()
        self.__add_balance_constraints()
        self.__add_capacity_constraints()
        self.__add_feasibility_constraints()
        self.__add_objective()
        self.model.optimize()
        self.status = self.model.status
        if self.model.status != GRB.INFEASIBLE:
            self.mip_gap = self.model.MIPGap
        if self.model.status == GRB.OPTIMAL:
            self.obj_val = self.model.objVal

    def __add_variables(self):
        # integer flow variables
        x = self.model.addVars(((aux_timed_arc.id, com.id) for com in self.K.values()
                                for aux_timed_arc in list(com.E_k_S.values()) + list(com.F_k_S.values())),
                               vtype=GRB.BINARY, name='x{0}_{1}')

        # integer truck count variables
        y = self.model.addVars((timed_arc.id for timed_arc in self.A_S.values()), vtype=GRB.INTEGER, lb=0, name='y{0}')
        self.x = x
        self.y = y
        self.vars.append(len(x))
        self.vars.append(len(y))

    def __add_balance_constraints(self):
        flow_conservation = self.model.addConstrs(
            gp.quicksum(self.x[aux_timed_arc_id, com.id] for aux_timed_arc_id in
                        set(aux_timed_node.in_timed_arcs).intersection(set(com.E_F_k_S)))
            - gp.quicksum(self.x[aux_timed_arc_id, com.id] for aux_timed_arc_id in
                          set(aux_timed_node.out_timed_arcs).intersection(set(com.E_F_k_S)))
            == 0 for com in self.K.values() for aux_timed_node in com.V_k_S_internal.values())

        flow_origin = self.model.addConstrs(
            gp.quicksum(self.x[aux_timed_arc_id, com.id] for aux_timed_arc_id in
                        set(aux_timed_node.in_timed_arcs).intersection(set(com.E_F_k_S)))
            - gp.quicksum(self.x[aux_timed_arc_id, com.id] for aux_timed_arc_id in
                          set(aux_timed_node.out_timed_arcs).intersection(set(com.E_F_k_S)))
            == -1 for com in self.K.values() for aux_timed_node in com.timed_origin.values())

        flow_destination = self.model.addConstrs(
            gp.quicksum(self.x[aux_timed_arc_id, com.id] for aux_timed_arc_id in
                        set(aux_timed_node.in_timed_arcs).intersection(set(com.E_F_k_S)))
            - gp.quicksum(self.x[aux_timed_arc_id, com.id] for aux_timed_arc_id in
                          set(aux_timed_node.out_timed_arcs).intersection(set(com.E_F_k_S)))
            == 1 for com in self.K.values() for aux_timed_node in com.timed_destination.values())

        self.constraints.append(len(flow_conservation))
        self.constraints.append(len(flow_origin))
        self.constraints.append(len(flow_destination))

    def __add_capacity_constraints(self):
        arc_capacities = self.model.addConstrs(
            gp.quicksum(gp.quicksum(self.x[aux_timed_arc.id, com.id] * com.demand
                        for com in aux_timed_arc.commodities.values())
                        for aux_timed_arc in timed_arc.projected_set.values())
            <= timed_arc.capacity * self.y[timed_arc.id] for timed_arc in self.A_S.values())

        self.constraints.append(len(arc_capacities))

    def __add_feasibility_constraints(self):
        feasibility = self.model.addConstrs(
            gp.quicksum(self.x[aux_timed_arc.id, com.id] * aux_timed_arc.transit_time
                        for aux_timed_arc in com.E_k_S.values())
            <= com.deadline - com.release_time for com in self.K.values())
        self.constraints.append(len(feasibility))

    def __add_objective(self):
        self.model.setObjective(gp.quicksum(self.y[timed_arc.id] * timed_arc.fixed_cost
                                            for timed_arc in self.A_S.values()) +
                                gp.quicksum(self.x[aux_timed_arc.id, com.id] * aux_timed_arc.variable_cost[com.id]
                                            * com.demand
                                            for aux_timed_arc in self.E_S.values()
                                            for com in aux_timed_arc.commodities.values()),
                                GRB.MINIMIZE)

