

class SetGenerator:
    def __init__(self, Input_data, G_S, D_S):
        self.V = G_S.V
        self.V_S = G_S.V_S
        self.E = G_S.E
        self.E_S = G_S.E_S
        self.F = G_S.F
        self.F_S = G_S.F_S
        self.A_S = D_S.A_S

        self.timed_nodes = self.V_S.copy()
        self.E_F_S = self.E_S.copy()
        self.E_F_S.update(self.F_S)

        self.K = Input_data.K
        self.reset_sets()
        self.generate_sets()

    def generate_sets(self):
        self.generate_timed_copies()
        self.generate_G_k_S()
        self.generate_inbound_outbound_arcs()
        self.generate_projection_sets()

    def generate_timed_copies(self):
        for aux_node in self.V.values():
            aux_node.timed_copies = {}
        for aux_timed_node in self.V_S.values():
            base_node = aux_timed_node.base_node
            base_node.timed_copies[aux_timed_node.id] = aux_timed_node
        for aux_arc in list(self.E.values()) + list(self.F.values()):
            aux_arc.timed_copies = {}
        for aux_timed_arc in list(self.E_S.values()) + list(self.F_S.values()):
            base_arc = aux_timed_arc.base_arc
            base_arc.timed_copies[aux_timed_arc.id] = aux_timed_arc

    # --------------------------------------------------------- #
    #                       Generate G^k_S
    # --------------------------------------------------------- #
    def generate_G_k_S(self):
        self.__generate_V_k_S()
        self.__generate_E_k_S()
        self.__generate_F_k_S()
        self.__generate_E_F_k_S()
        self.__split_V_k_S()

    def __generate_V_k_S(self):
        for com in self.K.values():
            for aux_node in com.V_k.values():
                for aux_timed_node in aux_node.timed_copies.values():
                    com.V_k_S[aux_timed_node.id] = aux_timed_node

    def __generate_E_k_S(self):
        for com in self.K.values():
            for aux_base_arc in com.E_k.values():
                for aux_timed_arc in aux_base_arc.timed_copies.values():
                    com.E_k_S[aux_timed_arc.id] = aux_timed_arc
                    aux_timed_arc.commodities[com.id] = com

    def __generate_F_k_S(self):
        for com in self.K.values():
            for aux_base_arc in com.F_k.values():
                for aux_timed_arc in aux_base_arc.timed_copies.values():
                    com.F_k_S[aux_timed_arc.id] = aux_timed_arc
                    aux_timed_arc.commodities[com.id] = com

    def __generate_E_F_k_S(self):
        for com in self.K.values():
            com.E_F_k_S = com.E_k_S.copy()
            com.E_F_k_S.update(com.F_k_S)

    def __split_V_k_S(self):
        '''
        assigning origin and destination timed nodes, and internal nodes
        '''
        for com in self.K.values():
            for timed_node in com.V_k_S.values():
                if timed_node.time == com.release_time and timed_node.base_id == com.origin.id:
                    com.timed_origin[timed_node.id] = timed_node
                elif timed_node.time == com.deadline and timed_node.base_id == com.destination.id:
                    com.timed_destination[timed_node.id] = timed_node
                else:
                    com.V_k_S_internal[timed_node.id] = timed_node

    # --------------------------------------------------------- #
    #             Generate inbound-outbound arcs
    # --------------------------------------------------------- #
    def generate_inbound_outbound_arcs(self):
        '''
        Assigns the incoming and outgoing timed arcs for each timed node.
        '''
        for aux_timed_arc in self.E_F_S.values():
            origin_node = aux_timed_arc.origin
            destination_node = aux_timed_arc.destination
            origin_node.out_timed_arcs[aux_timed_arc.id] = aux_timed_arc
            destination_node.in_timed_arcs[aux_timed_arc.id] = aux_timed_arc

    # --------------------------------------------------------- #
    #             Generate \E_k sets per e \in A_S
    # --------------------------------------------------------- #
    def generate_projection_sets(self):
        for aux_timed_arc in self.E_S.values():
            time = aux_timed_arc.time
            arc_in_D = aux_timed_arc.base_arc.arc_in_D
            timed_arc = self.A_S[arc_in_D.id + '_' + str(time)]
            timed_arc.projected_set[aux_timed_arc.id] = aux_timed_arc
            aux_timed_arc.project_to_D_S = timed_arc

    # --------------------------------------------------------- #
    #               Resetting sets to be empty
    # --------------------------------------------------------- #

    def reset_sets(self):
        for com in self.K.values():
            com.V_k_S = {}
            com.E_k_S = {}
            com.F_k_S = {}
            com.E_F_k_S = {}
            com.timed_origin = {}
            com.timed_destination = {}
            com.V_k_S_internal = {}
        for aux_timed_arc in self.E_S.values():
            aux_timed_arc.commodities = {}
        for aux_timed_arc in self.F_S.values():
            aux_timed_arc.commodities = {}
        for timed_node in self.V_S.values():
            timed_node.out_timed_arcs = {}
            timed_node.in_timed_arcs = {}
        for timed_arc in self.A_S.values():
            timed_arc.projected_set = {}


