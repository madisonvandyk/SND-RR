import math
import pandas as pd

from Node import Node
from Arc import Arc
from Commodity import Commodity

# InputReader:
# Generates: Flat network: node_dict, arc_dict, path_dict, holdover_arc_dict


class InputReader:
    def __init__(self, instance_folder):
        self.instance_folder = instance_folder
        self.N = {}
        self.A = {}
        self.K = {}
        self.H = {}
        self.time_horizon_start = math.inf
        self.time_horizon_end = 0

        self.__read_input_parameters()
        self.__read_flat_instance()
        self.__generate_holdover_arcs()
        self.__compute_time_horizon()

    def __read_input_parameters(self):
        parameters_df = pd.read_csv(self.instance_folder + 'parameters.csv')
        self.Parameters = dict(zip(list(parameters_df.parameter_name), list(parameters_df.value)))
        for field in ['DP', 'GROUP_TIMES', 'REGIONAL']:
            self.__interpret_as_bool(field)

    def __interpret_as_bool(self, field):
        if not isinstance(self.Parameters[field], bool):
            if self.Parameters[field] == 'TRUE' or self.Parameters[field] == 'True':
                self.Parameters[field] = True
            else:
                self.Parameters[field] = False

    def __read_flat_instance(self):
        nodes = pd.read_csv(self.instance_folder + 'nodes.csv')
        for ind, row in nodes.iterrows():
            node = Node(row['id'])
            self.N[node.id] = node
            if self.Parameters['REGIONAL']:
                node.hub = row['hub']
                node.region_hub = row['region_hub']

        arcs = pd.read_csv(self.instance_folder + 'arcs.csv')
        variable_costs = pd.read_csv(self.instance_folder + 'variable_costs.csv')
        var_cost_dict = variable_costs.set_index('commodity').to_dict()
        for ind, row in arcs.iterrows():
            arc = Arc(row, self.N)
            origin_node = arc.origin
            origin_node.add_outgoing_arc(arc)
            arc.assign_var_costs(var_cost_dict[arc.id])
            self.A[arc.id] = arc

        commodities = pd.read_csv(self.instance_folder + 'commodities.csv')
        for ind, row in commodities.iterrows():
            commodity = Commodity(self.Parameters, row, self.N, self.A, True)
            commodity.assign_release_deadline(row['release_time'], row['deadline'])
            self.K[commodity.id] = commodity

    def __generate_holdover_arcs(self):
        for node in self.N.values():
            arc_data = {'id': str(node.id) + '_holdover',
                        'origin': node.id,
                        'destination': node.id,
                        'fixed_cost': 0,
                        'capacity': math.inf,
                        'transit_time': 1}
            arc_data = pd.Series(arc_data)
            arc = Arc(arc_data, self.N)
            self.H[arc.id] = arc

    def __compute_time_horizon(self):
        for commodity in self.K.values():
            if commodity.release_time < self.time_horizon_start:
                self.time_horizon_start = commodity.release_time
            if commodity.deadline > self.time_horizon_end:
                self.time_horizon_end = commodity.deadline

