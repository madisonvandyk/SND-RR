from TimedArc import TimedArc
from TimedNode import TimedNode


class TimedArcGenerator:
    def __init__(self, Parameters, Input_data, Aux_G, V_S, scenario):
        self.Input_data = Input_data
        self.N = Input_data.N
        self.N_S = {}
        self.V = Aux_G.V
        self.V_S = V_S

        self.__generate_N_S()
        if scenario == 'node_disc':
            self.__update_V_S()

        self.G_S = TimedAuxNetwork(Parameters, Input_data, Aux_G, self.V_S)
        self.D_S = TimedBaseNetwork(Parameters, Input_data, self.N_S)

    def __generate_N_S(self):
        for timed_aux_node in self.V_S.values():
            node_in_D = timed_aux_node.base_node.node_in_D
            timed_node = TimedNode(node_in_D, timed_aux_node.time)
            self.N_S[(timed_node.base_id, timed_node.time)] = timed_node

    # We obtain the original node-based DDD approach by forcing each node copy in G of a fixed node to
    # have the same set of departure times. To form this set we take the union of the departure times of the copies.
    def __update_V_S(self):
        self.V_S = {}
        for timed_node in self.N_S.values():
            base_node = timed_node.base_node
            for aux_node in base_node.node_copies.values():
                timed_node = TimedNode(aux_node, timed_node.time)
                self.V_S[(timed_node.base_id, timed_node.time)] = timed_node


# --------------------------------------------------------- #
#               Timed auxiliary network
# --------------------------------------------------------- #
class TimedAuxNetwork:
    def __init__(self, Parameters, Input_data, Aux_G, V_S):
        self.Parameters = Parameters
        self.K = Input_data.K
        self.time_horizon_start = Input_data.time_horizon_start
        self.time_horizon_end = Input_data.time_horizon_end

        # Tasks
        self.Aux_G = Aux_G
        self.V_S = V_S
        self.V = Aux_G.V
        self.E = Aux_G.E
        self.F = Aux_G.F
        self.E_S = {}
        self.F_S = {}
        self.generate_E_S()
        self.generate_F_S()

    # Generates arcs E_S given V_S
    def generate_E_S(self):
        for arc in self.E.values():
            origin_id = arc.origin_id
            destination_id = arc.destination_id
            for t in range(self.time_horizon_start, self.time_horizon_end + 1):
                if (origin_id, t) in self.V_S.keys():
                    if t + arc.transit_time <= self.time_horizon_end:
                        j = 0
                        while True:
                            if (destination_id, t + arc.transit_time - j) in self.V_S.keys():
                                timed_arc = TimedArc(arc, t, self.V_S, arc.transit_time - j)
                                self.E_S[timed_arc.id] = timed_arc
                                arc.timed_copies[timed_arc.id] = timed_arc
                                break
                            j += 1

    # Generates holdover arcs F_S given V_S
    def generate_F_S(self):
        for node in self.V.values():
            arc = self.F[str(node.id) + '_holdover']
            current = self.time_horizon_start
            while current <= self.time_horizon_end - 1:
                for t in range(current + 1, self.time_horizon_end + 1):
                    if (node.id, t) in self.V_S.keys():
                        timed_arc = TimedArc(arc, current, self.V_S, t - current)
                        self.F_S[timed_arc.id] = timed_arc
                        arc.timed_copies[timed_arc.id] = timed_arc
                        current = t


# --------------------------------------------------------- #
#               Timed base network
# --------------------------------------------------------- #
class TimedBaseNetwork:
    def __init__(self, Parameters, Input_data, N_S):
        self.Parameters = Parameters
        self.K = Input_data.K
        self.time_horizon_start = Input_data.time_horizon_start
        self.time_horizon_end = Input_data.time_horizon_end

        # Tasks
        self.N_S = N_S
        self.A = Input_data.A
        self.A_S = {}
        self.generate_A_S()

    # Generates arcs A_S given N_S
    def generate_A_S(self):
        for arc in self.A.values():
            origin_id = arc.origin_id
            destination_id = arc.destination_id
            for t in range(self.time_horizon_start, self.time_horizon_end + 1):
                if (origin_id, t) in self.N_S.keys():
                    if t + arc.transit_time <= self.time_horizon_end:
                        j = 0
                        while True:
                            if (destination_id, t + arc.transit_time - j) in self.N_S.keys():
                                timed_arc = TimedArc(arc, t, self.N_S, arc.transit_time - j)
                                self.A_S[timed_arc.id] = timed_arc
                                arc.timed_copies[timed_arc.id] = timed_arc
                                break
                            j += 1
