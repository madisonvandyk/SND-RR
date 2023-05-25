from gurobipy import GRB
import math
from TimedNode import TimedNode


class RefineDiscretization:
    def __init__(self, Input_data, G_S, LP_UB):
        self.Input_data = Input_data
        self.K = Input_data.K
        self.time_horizon_start = Input_data.time_horizon_start
        self.time_horizon_end = Input_data.time_horizon_end

        self.Aux_G = G_S.Aux_G
        self.V = self.Aux_G.V

        self.V_S = G_S.V_S
        self.E_S = G_S.E_S
        self.F_S = G_S.F_S
        self.LP_UB = LP_UB
        self.V_S_new = self.V_S.copy()
        self.newly_added = {}

        if self.LP_UB.model.status == GRB.INFEASIBLE:
            self.infeasible_commodities = self.K
        else:
            self.__gen_infeasible_commodities()
        self.__gen_short_to_lengthen()
        self.refine_V_S()
        if len(self.newly_added) == 0 and not self.LP_UB.is_feasible:
            quit('cycling: instance infeasible and no timed nodes added.')

    def __gen_infeasible_commodities(self):
        self.infeasible_commodities = {}
        for timed_arc in self.LP_UB.A_S_support.values():
            for com1, com2 in timed_arc.K_pairs:
                if self.LP_UB.delta[com1.id, com2.id, timed_arc.id].x >= 0.001:
                    self.infeasible_commodities[com1.id] = com1
                    self.infeasible_commodities[com2.id] = com2

    def __gen_short_to_lengthen(self):
        '''
        For each infeasible commodity, we lengthen the short timed aux arc
        with the earliest departure time
        '''
        self.short_to_lengthen = {}
        for k in self.infeasible_commodities.values():
            earliest_dep_arc = k.E_S_support[0]
            earliest_dep_time = math.inf
            for aux_timed_arc in k.E_S_support:
                if aux_timed_arc.red_time + 0.001 < aux_timed_arc.transit_time:
                    if aux_timed_arc.time < earliest_dep_time:
                        earliest_dep_arc = aux_timed_arc
                        earliest_dep_time = aux_timed_arc.time
            self.short_to_lengthen[earliest_dep_arc.id] = earliest_dep_arc

    def refine_V_S(self):
        '''
        adds timed auxiliary nodes to V_S to correct length of short aux timed
        arcs in self.short_to_lengthen
        '''
        for timed_arc in self.short_to_lengthen.values():
            t = timed_arc.time
            destination_node = self.V[timed_arc.destination_id]
            if t + timed_arc.transit_time < self.time_horizon_end:
                timed_node = TimedNode(destination_node, t + timed_arc.transit_time)
                if (timed_node.base_id, timed_node.time) not in self.V_S_new.keys():
                    self.V_S_new[(timed_node.base_id, timed_node.time)] = timed_node
                    self.newly_added[(timed_node.base_id, timed_node.time)] = timed_node







