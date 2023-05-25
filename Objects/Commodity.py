from ast import literal_eval


class Commodity:
    def __init__(self, Parameters, com_data, node_dict, arc_dict, lit_eval):
        # Input properties
        self.id = com_data.id
        self.demand = com_data.demand
        self.origin = node_dict[com_data.origin]
        self.destination = node_dict[com_data.destination]
        self.shortest_path_time = 0
        if Parameters['DP']:
            if lit_eval:
                self.arc_list = literal_eval(com_data.arc_list)
                self.node_list = literal_eval(com_data.node_list)
            else:
                self.arc_list = com_data.arc_list
                self.node_list = com_data.node_list
        self.release_time = 0
        self.deadline = 0

        # Timed data relative to time-expanded network
        self.timed_origin = {}
        self.timed_destination = {}

        # for generating the auxiliary network
        self.A_k = {}
        self.N_k = {}
        self.node_parts = {}
        self.out_arc_dict = {node_id: set() for node_id in node_dict.keys()}

        # feasible subgraph in the auxiliary network
        self.node_copies = {}
        self.V_k = {}
        self.E_k = {}
        self.F_k = {}

        # timed feasible auxiliary network
        self.V_k_S = {}
        self.E_k_S = {}
        self.F_k_S = {}
        self.E_F_k_S = {}
        self.V_k_S_internal = {}

        # From partial network solve
        self.E_S_support = []
        self.E_F_S_support = []
        self.ordered_E_S_support = []
        self.A_S_support = []
        self.ordered_A_support = []
        self.ordered_N_support = []
        self.node_set = {}

    def assign_shortest_path_time(self, time):
        self.shortest_path_time = time

    def assign_release_deadline(self, release_time, deadline):
        self.release_time = release_time
        self.deadline = deadline




