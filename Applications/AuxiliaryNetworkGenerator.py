import math
import pandas as pd
import networkx as nx

from Node import Node
from Arc import Arc


class AuxiliaryNetwork:
    def __init__(self, input_data, parameters):
        self.input_data = input_data
        self.parameters = parameters

        # original data in base graph, D
        self.N = input_data.N
        self.A = input_data.A
        self.K = input_data.K
        self.H = input_data.H
        self.time_horizon_start = input_data.time_horizon_start
        self.time_horizon_end = input_data.time_horizon_end

        # objects in auxiliary network, G
        self.V = {}
        self.E = {}
        self.F = {}

        # functions
        self.__generate_D_k()
        self.__create_aux_graph_G()
        self.__generate_G_k()

    # --------------------------------------------------------- #
    #                  Generate subgraph D^k
    # --------------------------------------------------------- #
    def __generate_D_k(self):
        '''
        Generates the subgraph D^k consisting of nodes and arcs that could be used by commodity k.
            - if designated paths, then D^k = P_k
            - if hub-and-spoke, then D^k is the set of national arcs and regional arcs
                for the origin and destination regions
            - otherwise D^k is equal to the arcs that could be possibly used by
                a feasible walk
        '''
        if self.parameters['DP']:
            self.__generate_A_k_for_DP()
        else:
            self.__generate_node_distances()
            self.__generate_A_k()
        if self.parameters['REGIONAL']:
            self.__refine_A_k_for_regional()
        self.__generate_N_k()

    def __generate_A_k_for_DP(self):
        for com in self.K.values():
            com.A_k = {}
            for arc_id in com.arc_list:
                arc = self.A[arc_id]
                com.A_k[arc_id] = arc

    def __generate_node_distances(self):
        '''
        for each node-pair (v,w), stores whether there is a dipath from v to w in D
        stored in the node. reachable dict field, the value is the transit time of the shortest path
        '''
        self.D = nx.DiGraph()
        self.D.add_nodes_from(self.N.keys())
        for arc in self.A.values():
            self.D.add_edge(arc.origin_id, arc.destination_id, length=arc.transit_time, name=arc.id)
        for node1 in self.N.values():
            for node2 in self.N.values():
                if nx.has_path(self.D, node1.id, node2.id):
                    L = nx.shortest_path_length(self.D, node1.id, node2.id, weight='length')
                    node1.dist_to_node[node2.id] = L
                else:
                    node1.dist_to_node[node2.id] = math.inf

    def __generate_A_k(self):
        for commodity in self.K.values():
            for arc in self.A.values():
                if arc.origin != commodity.destination and arc.destination != commodity.origin:
                    L1 = commodity.origin.dist_to_node[arc.origin.id]
                    L2 = arc.destination.dist_to_node[commodity.destination.id]
                    max_len = commodity.deadline - commodity.release_time
                    if L1 + arc.transit_time + L2 <= max_len:
                        commodity.A_k[arc.id] = arc

    def __refine_A_k_for_regional(self):
        for com in self.K.values():
            original_A_k = com.A_k
            com.A_k = {}
            origin_region = com.origin.region_hub
            destination_region = com.destination.region_hub
            for arc in original_A_k.values():
                arc_region = arc.origin.region_hub
                if arc.origin.hub and arc.destination.hub:
                    com.A_k[arc.id] = arc
                elif (arc_region == origin_region) or (arc_region == destination_region):
                    com.A_k[arc.id] = arc

    def __generate_N_k(self):
        for commodity in self.K.values():
            for arc in commodity.A_k.values():
                commodity.N_k[arc.origin.id] = arc.origin
                commodity.N_k[arc.destination.id] = arc.destination

    # --------------------------------------------------------- #
    #               Generate auxiliary graph G
    # --------------------------------------------------------- #

    def __create_aux_graph_G(self):
        self.__partition_arcs()
        self.__create_aux_nodes()
        self.__create_aux_arcs()
        self.__create_aux_holdover_arcs()

    def __partition_arcs(self):
        for node in self.N.values():
            out_arcs = list(node.outgoing_arcs.keys())
            self.__partition_out_arcs(node, out_arcs)
            node.parts.add(0)
            for arc_id in out_arcs:
                arc = self.A[arc_id]
                node.parts.add(arc.part_num)

    def __partition_out_arcs(self, node, out_arcs):
        '''
        Constructs the arc partition of the out_arcs departing the given node
        Stores the part for each arc in out_arcs in the arc.part_num field.
        '''
        # initially assigning all arcs to their own part
        for i in range(len(out_arcs)):
            arc = self.A[out_arcs[i]]
            arc.part_num = i + 1
        # merging the parts when some commodity could use two arcs in different parts
        for commodity in self.K.values():
            arc_subset = set(node.outgoing_arcs.keys()).intersection(commodity.A_k.keys())
            # find min part num of an arc in the set and merge all arcs in parts hit by this commodity to that min part.
            commodity.out_arc_dict[node.id] = arc_subset
            min_val = math.inf
            part_nums_to_merge = set()
            for arc_id in arc_subset:
                arc = self.A[arc_id]
                part_nums_to_merge.add(arc.part_num)
                if arc.part_num < min_val:
                    min_val = arc.part_num
            for arc_id in out_arcs:
                arc = self.A[arc_id]
                if arc.part_num in part_nums_to_merge:
                    arc.part_num = min_val

    def __create_aux_nodes(self):
        for node in self.N.values():
            for i in node.parts:
                self.__create_aux_node(node, i)

    def __create_aux_node(self, base_node, num):
        aux_node_id = str(num) + base_node.id
        aux_node = Node(aux_node_id)
        aux_node.num = num
        aux_node.set_node_in_D(base_node)
        self.V[aux_node.id] = aux_node
        base_node.add_node_copy(aux_node)

    def __create_aux_arcs(self):
        '''
        Creates a copy of each arc for each copy of the destination node,
        and each departs the copy of the origin for that arc
        '''
        for arc in self.A.values():
            # find the part in the source node that contains this arc
            part = arc.part_num
            aux_origin = self.V[str(part) + arc.origin.id]
            for aux_destination in arc.destination.node_copies.values():
                self.__create_aux_arc(arc, aux_origin, aux_destination)

    def __create_aux_arc(self, base_arc, aux_origin, aux_destination):
        arc_id = str(aux_destination.num) + base_arc.id
        arc_attributes = {'id': arc_id, 'origin': aux_origin.id, 'destination': aux_destination.id,
                          'fixed_cost': base_arc.fixed_cost, 'capacity': base_arc.capacity,
                          'transit_time': base_arc.transit_time}
        aux_arc = Arc(pd.Series(arc_attributes), self.V)
        aux_arc.variable_cost = base_arc.variable_cost
        base_arc.add_arc_copy(aux_arc)
        aux_arc.set_arc_in_D(base_arc)
        self.E[aux_arc.id] = aux_arc

    def __create_aux_holdover_arcs(self):
        for aux_node in self.V.values():
            arc_data = {'id': str(aux_node.id) + '_holdover',
                        'origin': aux_node.id,
                        'destination': aux_node.id,
                        'fixed_cost': 0,
                        'capacity': math.inf,
                        'transit_time': 1}
            arc_data = pd.Series(arc_data)
            arc = Arc(arc_data, self.V)
            self.F[arc.id] = arc

    # --------------------------------------------------------- #
    #                       Generate G^k
    # --------------------------------------------------------- #
    def __generate_G_k(self):
        self.__generate_V_k()
        self.__generate_E_k()
        self.__generate_F_k()
        self.__assign_aux_source_sinks()

    def __generate_V_k(self):
        for com in self.K.values():
            com.V_k = {}
            for node in com.N_k.values():
                # find aux node copy for that node
                if len(com.out_arc_dict[node.id]) > 0:
                    arc_id = com.out_arc_dict[node.id].pop()
                    arc = self.A[arc_id]
                    part_num = arc.part_num
                else:
                    part_num = 0
                com.node_parts[node.id] = part_num
                aux_node_id = str(part_num) + node.id
                aux_node = self.V[aux_node_id]
                com.V_k[aux_node.id] = aux_node
                com.node_copies[node.id] = aux_node

    def __generate_E_k(self):
        for com in self.K.values():
            for arc in com.A_k.values():
                destination = arc.destination
                aux_destination = com.node_copies[destination.id]
                aux_arc_id = str(aux_destination.num) + arc.id
                aux_arc = self.E[aux_arc_id]
                com.E_k[aux_arc_id] = aux_arc

    def __generate_F_k(self):
        for com in self.K.values():
            for aux_node in com.V_k.values():
                aux_holdover_id = str(aux_node.id) + '_holdover'
                holdover_arc = self.F[aux_holdover_id]
                com.F_k[aux_holdover_id] = holdover_arc

    def __assign_aux_source_sinks(self):
        for com in self.K.values():
            origin_part = com.node_parts[com.origin.id]
            com_origin_id = str(origin_part) + com.origin.id
            com_destination_id = str(0) + com.destination.id
            aux_origin = self.V[com_origin_id]
            aux_destination = self.V[com_destination_id]
            com.origin = aux_origin
            com.destination = aux_destination




