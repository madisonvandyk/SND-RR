from TimedNode import TimedNode
import bisect

# Generates initial partial (aux) timed node set: V_S


class GenerateTimedNodes:
    def __init__(self, Input_data, aux_graph):
        self.K = Input_data.K
        self.V = aux_graph.V
        self.time_horizon_start = Input_data.time_horizon_start
        self.time_horizon_end = Input_data.time_horizon_end

        self.V_S = {}
        self.V_S_by_base = {base_id: [] for base_id in self.V.keys()}
        self.generate_V_S()

    def generate_V_S(self):
        # adding timed nodes at start and end of time horizon
        for node in self.V.values():
            self.insert_timed_node(node, self.time_horizon_start)
            self.insert_timed_node(node, self.time_horizon_end)
        # adding timed nodes at commodity release times and deadlines
        for commodity in self.K.values():
            self.insert_timed_node(commodity.origin, commodity.release_time)
            self.insert_timed_node(commodity.destination, commodity.deadline)

    def insert_timed_node(self, node, node_time):
        timed_node = TimedNode(node, node_time)
        self.V_S[(timed_node.base_id, timed_node.time)] = timed_node
        times = self.V_S_by_base[timed_node.base_id]
        if node_time not in times:
            bisect.insort(times, node_time)
        self.V_S_by_base[timed_node.base_id] = times
        node.timed_copies[timed_node.id] = timed_node


