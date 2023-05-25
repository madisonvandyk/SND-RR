import gurobipy as gp
from gurobipy import GRB
import math
from itertools import combinations


class UpperBound:
    def __init__(self, Input_data, G_S, IP_S):
        self.Input_data = Input_data
        self.K = Input_data.K
        self.A = Input_data.A
        self.H = Input_data.H
        self.N = Input_data.N

        self.time_horizon_start = Input_data.time_horizon_start
        self.time_horizon_end = Input_data.time_horizon_end

        # objects in G_S
        self.V_S = G_S.V_S
        self.E_S = G_S.E_S
        self.F_S = G_S.F_S

        self.IP_S = IP_S
        self.D_S_support = {}
        self.short_arcs = {}
        self.is_feasible = False
        self.__generate_paths_in_D()
        self.__gen_timed_arc_overlap_pairs()
        self.__gen_fixed_times()

        self.model = gp.Model('SND_continuous')
        self.__solve_continuous_formulation()

        self.UB = math.inf
        if self.model.status != GRB.INFEASIBLE:
            self.__gen_upper_bound()
            if self.model.objVal == 0:
                self.is_feasible = True

    # --------------------------------------------------------- #
    #            Generate path in D for each commodity
    # --------------------------------------------------------- #

    def __generate_paths_in_D(self):
        self.__generate_E_S_support()
        self.__order_E_S_support()
        self.__map_support_to_A_S()
        self.__order_A_support()
        self.__order_N_support()

    def __generate_E_S_support(self):
        # Computes the set of timed arcs used in the solution for each commodity
        self.E_S_support = {}
        for com in self.K.values():
            com.E_S_support = []
            com.E_F_S_support = []
            for aux_timed_arc in com.E_F_k_S.values():
                if self.IP_S.x[aux_timed_arc.id, com.id].x >= 0.001:
                    com.E_F_S_support.append(aux_timed_arc)
                    if aux_timed_arc in self.E_S.values():
                        com.E_S_support.append(aux_timed_arc)
                        self.E_S_support[aux_timed_arc.id] = aux_timed_arc

    def __order_E_S_support(self):
        for com in self.K.values():
            com.ordered_E_S_support = []
            origin_timed_node = self.V_S[com.origin.id, com.release_time]
            destination_timed_node = self.V_S[com.destination.id, com.deadline]
            current_timed_node = origin_timed_node
            while current_timed_node != destination_timed_node:
                for aux_timed_arc in com.E_F_S_support:
                    if aux_timed_arc.origin == current_timed_node:
                        if aux_timed_arc in self.E_S.values():
                            com.ordered_E_S_support.append(aux_timed_arc)
                            com.E_F_S_support.remove(aux_timed_arc)
                        current_timed_node = aux_timed_arc.destination
                        break

    def __map_support_to_A_S(self):
        for com in self.K.values():
            com.A_S_support = []
            for aux_timed_arc in com.E_S_support:
                timed_arc = aux_timed_arc.project_to_D_S
                com.A_S_support.append(timed_arc)

    def __order_A_support(self):
        for com in self.K.values():
            com.ordered_A_support = []
            for aux_timed_arc in com.ordered_E_S_support:
                timed_arc = aux_timed_arc.project_to_D_S
                base_arc = timed_arc.base_arc
                com.ordered_A_support.append(base_arc)

    def __order_N_support(self):
        for com in self.K.values():
            com.ordered_N_support = [com.origin.node_in_D]
            com.node_set = {com.origin.node_in_D.id: com.origin.node_in_D}
            for arc in com.ordered_A_support:
                com.ordered_N_support.append(arc.destination)
                if arc.destination.id not in com.node_set.keys():
                    com.node_set[arc.destination.id] = arc.destination

    # --------------------------------------------------------- #
    #       Generate overlapping commodities at each arc
    # --------------------------------------------------------- #
    def __gen_timed_arc_overlap_pairs(self):
        self.A_S_support = {}
        for com in self.K.values():
            for timed_arc in com.A_S_support:
                if timed_arc.origin_id in com.node_set.keys():
                    timed_arc.K_in_support[com.id] = com
                    self.A_S_support[timed_arc.id] = timed_arc
        for timed_arc in self.A_S_support.values():
            timed_arc.K_pairs = list(combinations(timed_arc.K_in_support.values(), 2))

    # --------------------------------------------------------- #
    #            Determine feasible trajectories
    # --------------------------------------------------------- #

    def __gen_fixed_times(self):
        self.__compute_short_timed_arcs()
        self.__compute_feasible_commodities()

    def __compute_short_timed_arcs(self):
        """
        Computes short arcs in the support of IP_G_S
        """
        self.short_arcs = {}
        for aux_timed_arc in self.E_S_support.values():
            if aux_timed_arc.red_time + 0.01 < aux_timed_arc.transit_time:
                self.short_arcs[aux_timed_arc.id] = aux_timed_arc
        print('short / total:', len(self.short_arcs.keys()), '/', len(self.E_S_support.keys()))

    def __compute_feasible_commodities(self):
        '''
        computes the list of commodities with no violated timed arcs
        '''
        self.feasible_commodities = []
        infeasible_timed_arc_keys = list(self.short_arcs.keys())
        for commodity in self.K.values():
            feasible = True
            for aux_timed_arc in commodity.E_S_support:
                if aux_timed_arc.id in infeasible_timed_arc_keys:
                    feasible = False
            if feasible:
                self.feasible_commodities.append(commodity)

    # --------------------------------------------------------- #
    #        Generate and solve continuous formulation
    # --------------------------------------------------------- #
    def __solve_continuous_formulation(self):
        self.model.Params.OutputFlag = 0
        self.model.Params.MIPgap = 0.01
        self.model.Params.TimeLimit = 7200
        self.status = 'status'
        self.mip_gap = 100
        self.obj_val = 0
        self.solution = None
        self.UB = math.inf
        self.__add_variables()
        self.is_feasible = False
        self.__add_constraints()
        self.__add_objective()
        self.model.optimize()

    def __add_variables(self):
        # continuous variable for each non-terminal node in (support) path of commodity
        t = self.model.addVars(((com.id, node_id)
                                for com in self.K.values()
                                for node_id in com.node_set.keys()),
                               vtype=GRB.CONTINUOUS, lb=0, name='t{0}_{1}')
        delta = self.model.addVars(((com1.id, com2.id, timed_arc.id)
                                    for timed_arc in self.A_S_support.values()
                                    for com1, com2 in timed_arc.K_pairs),
                                   vtype=GRB.CONTINUOUS, name='delta{0}_{1}_{2}')
        self.t = t
        self.delta = delta

    def __add_constraints(self):
        # release time feasible
        release_time = self.model.addConstrs(self.t[com.id, com.ordered_N_support[0].id]
                                             >= com.release_time
                                             for com in self.K.values())
        # deadline is feasible
        deadline = self.model.addConstrs(self.t[com.id, com.ordered_N_support[-1].id]
                                         <= com.deadline
                                         for com in self.K.values())

        # transit times obeyed
        transit_times = self.model.addConstrs(self.t[com.id, com.ordered_N_support[i].id]
                                              + com.ordered_A_support[i].transit_time
                                              <= self.t[com.id, com.ordered_N_support[i+1].id]
                                              for com in self.K.values()
                                              for i in range(0, len(com.ordered_N_support) - 1))

        # delta
        delta_const1 = self.model.addConstrs(self.delta[com1.id, com2.id, timed_arc.id]
                                             >= self.t[com1.id, timed_arc.base_arc.origin.id]
                                             - self.t[com2.id, timed_arc.base_arc.origin.id]
                                             for timed_arc in self.A_S_support.values()
                                             for com1, com2 in timed_arc.K_pairs)
        # second delta inequality
        delta_const2 = self.model.addConstrs(self.delta[com1.id, com2.id, timed_arc.id]
                                             >= self.t[com2.id, timed_arc.base_arc.origin.id]
                                             - self.t[com1.id, timed_arc.base_arc.origin.id]
                                             for timed_arc in self.A_S_support.values()
                                             for com1, com2 in timed_arc.K_pairs)
        # fix feasible times
        fixed_feasible_times = self.model.addConstrs(self.t[com.id, aux_timed_arc.origin.base_node.node_in_D.id]
                                                     == aux_timed_arc.time
                                                     for com in self.feasible_commodities
                                                     for aux_timed_arc in com.ordered_E_S_support)

    def __add_objective(self):
        self.model.setObjective(gp.quicksum(self.delta[com1.id, com2.id, timed_arc.id]
                                            for timed_arc in self.A_S_support.values()
                                            for com1, com2 in timed_arc.K_pairs), GRB.MINIMIZE)

    # --------------------------------------------------------- #
    #               Compute upper bound value
    # --------------------------------------------------------- #
    def __gen_upper_bound(self):
        variable_cost = 0
        for com in self.K.values():
            for arc in com.ordered_A_support:
                variable_cost += arc.variable_cost[com.id] * com.demand
        fixed_cost = 0
        for arc in self.A.values():
            arc.UB_times = {}
        for com in self.K.values():
            for arc in com.ordered_A_support:
                time_departed = round(self.t[com.id, arc.origin.id].x, 2)
                if time_departed in arc.UB_times.keys():
                    arc.UB_times[time_departed] += com.demand
                else:
                    arc.UB_times[time_departed] = com.demand
        for arc in self.A.values():
            for departure_time in arc.UB_times.keys():
                total_flow = arc.UB_times[departure_time]
                trucks_needed = math.ceil(total_flow / arc.capacity)
                fixed_cost += trucks_needed * arc.fixed_cost
        self.UB = fixed_cost + variable_cost






