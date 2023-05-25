import itertools
import pandas as pd
import random
import numpy as np
import networkx as nx
import os
import csv
import copy
import math
import bisect

from Node import Node
from Arc import Arc
from Commodity import Commodity

# --------------------------------------------------------- #
#               Flat instance parameters
# --------------------------------------------------------- #
# (n, h) [m, k]. h is set to 0 for non-regional instances
DP_flat_parameters = {(20, 0): [[230, 300], [150, 200]],
                      (25, 0): [[360, 480], [250, 300]]}
regional_flat_parameters = {(20, 3): [[70, 95], [100]],
                            (20, 4): [[55, 75], [100]],
                            (20, 5): [[50, 65], [100]],
                            (20, 6): [[45, 60], [100]]} #
SND_flat_parameters = {(20, 0): [[230, 300], [150, 200]]}
cost_target = {'F': 0.1, 'V': 0.05}
cap_target = {'L': 1, 'T': 8}

# --------------------------------------------------------- #
#               Timed instance parameters
# --------------------------------------------------------- #
e_sigma_factors = [1/9, 1/6, 1/3]
f_mean_factors = [1/4, 3/8]
f_sigma_factor = 1/6
deltas = [1]
scale_fixed_cost = 0.55


class InstanceGen:
    def __init__(self, Parameters):
        self.Parameters = Parameters
        self.FlatInstances = []
        input_folder = Parameters['INSTANCE_FOLDER']
        if not os.path.isdir(os.getcwd() + input_folder):
            os.mkdir(os.getcwd() + input_folder)
        self.__generate_flat_instances()
        self.__generate_timed_instances()

    def __generate_flat_instances(self):
        if self.Parameters['DP']:
            flat_parameters = DP_flat_parameters
            self.l = 100
            self.fixed_times = [0]
        elif self.Parameters['REGIONAL']:
            flat_parameters = regional_flat_parameters
            self.l = 30
            self.fixed_times = [0]
        else:
            flat_parameters = SND_flat_parameters
            self.l = 30
            self.fixed_times = [5, 10]

        n_h_m_k_tuples = []
        for key in flat_parameters.keys():
            n = key[0]
            h = key[1]
            for m in flat_parameters[key][0]:
                for k in flat_parameters[key][1]:
                    n_h_m_k_tuples.append([n, h, m, k])
        count = 0
        for [n, h, m, k] in n_h_m_k_tuples:
            for [cost, capacity] in itertools.product(['F', 'V'], ['L', 'T']):
                count += 1
                FlatInstance = CreateFlatInstance(self.Parameters, count, n, h, m, k, cost, capacity, self.l)
                print('Flat instance', count, ' generated')
                self.FlatInstances.append(FlatInstance)

    def __generate_timed_instances(self):
        for FlatInstance in self.FlatInstances:
            count = 0
            for [f_mean_factor, e_sigma_factor, delta, num_fixed_times] in \
                    itertools.product(f_mean_factors, e_sigma_factors, deltas, self.fixed_times):
                CreateTimedInstance(self.Parameters, count, copy.deepcopy(FlatInstance),
                                    e_sigma_factor, f_mean_factor, f_sigma_factor, delta, num_fixed_times)
                count += 1


class CreateFlatInstance:
    def __init__(self, Parameters, count, n, h, m, k, cost, capacity, l):
        self.id = 'Instance-' + str(count)
        self.n = n
        self.h = h
        self.m = m
        self.k = k
        self.l = l
        self.cost = cost
        self.capacity = capacity
        self.cap_target = cap_target[capacity]
        self.cost_target = cost_target[cost]
        self.Parameters = Parameters

        self.D = nx.DiGraph()
        self.node_dict = {}
        self.nodes = []
        self.arc_dict = {}
        self.com_dict = {}
        self.total_path_len = 0
        self.ave_path_len = 0

        self.generate_nodes()
        if self.Parameters['REGIONAL']:
            self.__select_hubs()
            self.__designate_regions()
            self.__check_arc_count()
        self.__generate_arcs()
        self.generate_commodities()
        self.scale_arc_data()
        instance_folder = self.Parameters['INSTANCE_FOLDER']
        self.instance_folder = os.getcwd() + instance_folder + self.id + '/'
        if not os.path.isdir(self.instance_folder):
            os.mkdir(self.instance_folder)

    def generate_nodes(self):
        for i in range(0, self.n):
            node_id = 'node_' + str(i)
            node = Node(node_id)
            # x and y only used for region-based networks
            x = np.random.random_integers(0, self.l - 1)
            y = np.random.random_integers(0, self.l - 1)
            node.x = x
            node.y = y
            self.node_dict[node.id] = node
            self.nodes.append(node.id)
        self.D.add_nodes_from(self.nodes)

    def __select_hubs(self):
        self.hubs = []
        node_objects = list(self.node_dict.values())
        count = 0
        while count < self.h:
            node = random.choice(node_objects)
            if node not in self.hubs:
                node.hub = True
                self.hubs.append(node)
                count += 1

    def __designate_regions(self):
        '''
        regions are represented by the hub node, nodes are assigned to the nearest hub
        '''
        for node in self.node_dict.values():
            if node.hub:
                node.region_hub = node
                node.region_size += 1
            else:
                # find pairwise distances.
                min_distance = math.inf
                nearest_hub = None
                for hub in self.hubs:
                    distance_to_hub = np.abs(node.y - hub.y) + np.abs(node.x - hub.x)
                    if distance_to_hub < min_distance:
                        min_distance = distance_to_hub
                        nearest_hub = hub
                node.region_hub = nearest_hub
                nearest_hub.region_size += 1

    def __check_arc_count(self):
        '''
        sets the number of arcs to the min of the number of possible arcs and the original arc count
        '''
        inter_regional = self.h * (self.h - 1)
        intra_regional = 0
        for hub in self.hubs:
            intra_regional += hub.region_size * (hub.region_size - 1)
        total_possible = intra_regional + inter_regional
        self.m = min(total_possible, self.m)

    def __generate_arcs(self):
        count = 0
        node_objects = list(self.node_dict.values())
        self.ordered_pairs = []
        if self.Parameters['REGIONAL']:
            # add all national arcs
            for node1 in self.hubs:
                for node2 in self.hubs:
                    if node1 != node2 and [node1.id, node2.id] not in self.ordered_pairs:
                        self.__add_arc(node1, node2, count)
                        count += 1
        while count < self.m:
            node1 = random.choice(node_objects)
            node2 = random.choice(node_objects)
            if node1 != node2 and [node1.id, node2.id] not in self.ordered_pairs:
                if self.Parameters['REGIONAL']:
                    if node1.region_hub.id == node2.region_hub.id:
                        self.__add_arc(node1, node2, count)
                        count += 1
                else:
                    self.__add_arc(node1, node2, count)
                    count += 1

    def __add_arc(self, node1, node2, arc_count):
        if self.Parameters['REGIONAL']:
            distance = np.abs(node2.y - node1.y) + np.abs(node2.x - node1.x)
            fixed_cost = distance * scale_fixed_cost
        else:
            fixed_cost = np.random.random_integers(1, self.l)
            distance = round(fixed_cost / scale_fixed_cost, 0)
        variable_cost = {}
        count = 1
        while count <= self.k:
            variable_cost['k_' + str(count)] = np.random.random_integers(1, 100)
            count += 1
        capacity = round(np.random.random_integers(1, self.l), 2)
        transit_time = distance
        arc_data = {'id': 'e_' + str(arc_count),
                    'origin': node1.id,
                    'destination': node2.id,
                    'fixed_cost': fixed_cost,
                    'capacity': capacity,
                    'transit_time': transit_time}
        arc = Arc(pd.Series(arc_data), self.node_dict)
        arc.assign_var_costs(variable_cost)
        self.arc_dict[arc.id] = arc
        self.ordered_pairs.append([node1.id, node2.id])
        self.D.add_edge(node1.id, node2.id, length=transit_time, id=arc.id)

    def generate_commodities(self):
        count = 0
        node_objects = list(self.node_dict.values())
        while count < self.k:
            node1 = random.choice(node_objects)
            node2 = random.choice(node_objects)
            if node1 != node2:
                demand = np.random.random_integers(1, 100)
                if nx.has_path(self.D, node1.id, node2.id):
                    L, arc_list, node_list = self.compute_shortest_commodity_path(node1.id, node2.id)
                    com_data = {'id': 'k_' + str(count),
                                'origin': node1.id,
                                'destination': node2.id,
                                'demand': demand,
                                'arc_list': arc_list,
                                'node_list': node_list}
                    commodity = Commodity(self.Parameters, pd.Series(com_data), self.node_dict, self.arc_dict, False)
                    commodity.assign_shortest_path_time(L)
                    self.com_dict[commodity.id] = commodity
                    count += 1
                    self.total_path_len += L
        self.ave_path_len = self.total_path_len / self.k

    def compute_shortest_commodity_path(self, origin_id, destination_id):
        node_list = nx.shortest_path(self.D, origin_id, destination_id, 'length')
        arc_list = []
        L = 0
        i = 0
        while i < len(node_list) - 1:
            arc_id = self.D[node_list[i]][node_list[i + 1]]['id']
            L += self.arc_dict[arc_id].transit_time
            arc_list.append(arc_id)
            i += 1
        return L, arc_list, node_list

    def scale_arc_data(self):
        total_demand = 0
        total_capacity = 0
        total_fixed_cost = 0
        total_var_cost = 0
        for commodity in self.com_dict.values():
            total_demand += commodity.demand
        for arc in self.arc_dict.values():
            total_capacity += arc.capacity
            total_fixed_cost += arc.fixed_cost
            total_var_cost += arc.sum_variable_costs
        # scaling capacities
        cap_ratio = self.m * total_demand / total_capacity
        cap_factor_scale = cap_ratio / self.cap_target
        for arc in self.arc_dict.values():
            arc.capacity = arc.capacity * cap_factor_scale
        # scaling costs
        cost_ratio = self.m * total_fixed_cost / (total_demand * total_var_cost)
        cost_factor_scale = cost_ratio / self.cost_target
        for arc in self.arc_dict.values():
            arc.fixed_cost = arc.fixed_cost / cost_factor_scale


class CreateTimedInstance:
    def __init__(self, Parameters, count, FlatInstance,
                 e_sigma_factor, f_mean_factor, f_sigma_factor, delta, num_fixed_times):
        self.Parameters = Parameters
        self.id = str(count)
        self.folder = FlatInstance.instance_folder + '/' + self.id + '/'
        self.FlatInstance = FlatInstance
        self.e_sigma_factor = e_sigma_factor
        self.f_mean_factor = f_mean_factor
        self.f_sigma_factor = f_sigma_factor
        self.delta = delta
        self.num_fixed_times = num_fixed_times
        self.feasible = True

        self.assign_release_deadline()
        if self.Parameters['GROUP_TIMES']:
            self.__group_times()
        self.write_instance()

    def assign_release_deadline(self):
        L = self.FlatInstance.ave_path_len
        for commodity in self.FlatInstance.com_dict.values():
            e_sigma = self.e_sigma_factor * L
            release_time = np.random.normal(L, e_sigma)
            while release_time > L + 3 * e_sigma or release_time < L - 3 * e_sigma:
                release_time = np.random.normal(L, e_sigma)
            commodity.release_time = math.ceil(commodity.release_time)
            f_mean = self.f_mean_factor * L
            f_sigma = f_mean * self.f_sigma_factor
            flexibility = np.random.normal(f_mean, f_sigma)
            while flexibility > f_mean + 3 * f_sigma or flexibility < f_mean - 3 * f_sigma:
                flexibility = np.random.normal(f_mean, f_sigma)
            commodity.deadline = commodity.release_time + commodity.shortest_path_time + flexibility
            commodity.deadline = math.floor(commodity.deadline)

    def __group_times(self):
        '''
        picks a set of p times for each node for release times and deadlines
        each is chosen uniformly at random from the i-th interval of times when the time horizon
        is split into p segments
        Then the commodity release times and deadlines are rounded down and up to the nearest critical time.
        '''
        # find start and end of time horizon
        start = math.inf
        end = 0
        for com in self.FlatInstance.com_dict.values():
            if com.release_time < start:
                start = com.release_time
            if com.deadline > end:
                end = com.deadline
        # divide [start, end] into p even intervals
        time_points = list(range(start, end + 1))  # create a list of consecutive integers from 1 to n
        subarrays = np.array_split(time_points, self.num_fixed_times)
        even_pieces = [subarray.tolist() for subarray in subarrays]
        for node in self.FlatInstance.node_dict.values():
            node.release_times = [random.choice(piece) for piece in even_pieces]
            node.release_times.insert(0, start)
            node.deadlines = [random.choice(piece) for piece in even_pieces]
            node.deadlines.append(end)
        for com in self.FlatInstance.com_dict.values():
            release_times = com.origin.release_times
            deadlines = com.destination.deadlines
            index1 = bisect.bisect_right(release_times, com.release_time) - 1
            com.release_time = release_times[index1]
            index2 = bisect.bisect_left(deadlines, com.deadline)
            com.deadline = deadlines[index2]

    def write_instance(self):
        if not os.path.isdir(self.folder):
            os.mkdir(self.folder)
        self.write_arcs()
        self.write_nodes()
        self.write_commodities()
        self.write_variable_costs()
        self.write_parameters()

    def write_nodes(self):
        with open(self.folder + 'nodes.csv', "w+") as f_out:
            names = ['id', 'hub', 'region_hub']
            csw = csv.DictWriter(f_out, names)
            csw.writeheader()
            for node in self.FlatInstance.node_dict.values():
                if self.Parameters['REGIONAL']:
                    line = {'id': node.id, 'hub': node.hub, 'region_hub': node.region_hub.id}
                else:
                    line = {'id': node.id}
                csw.writerow(line)

    def write_arcs(self):
        with open(self.folder + 'arcs.csv', "w+") as f_out:
            names = ['id', 'origin', 'destination', 'transit_time', 'capacity', 'fixed_cost', 'variable_cost']
            csw = csv.DictWriter(f_out, names)
            csw.writeheader()
            for arc in self.FlatInstance.arc_dict.values():
                line = {'id': arc.id,
                        'origin': arc.origin_id,
                        'destination': arc.destination_id,
                        'transit_time': arc.transit_time,
                        'capacity': arc.capacity,
                        'fixed_cost': arc.fixed_cost}
                csw.writerow(line)

    def write_variable_costs(self):
        var_cost_dict = {}
        for arc in self.FlatInstance.arc_dict.values():
            var_cost_dict[arc.id] = list(arc.variable_cost.values())
        dataframe = pd.DataFrame.from_dict(var_cost_dict)
        dataframe['commodity'] = self.FlatInstance.com_dict.keys()
        dataframe.set_index('commodity', inplace=True)
        dataframe.to_csv(self.folder + 'variable_costs.csv')

    def write_commodities(self):
        with open(self.folder + 'commodities.csv', "w+") as f_out:
            names = ['id', 'origin', 'destination', 'demand', 'release_time', 'deadline']
            if self.Parameters['DP']:
                names.append('arc_list')
                names.append('node_list')
            csw = csv.DictWriter(f_out, names)
            csw.writeheader()
            for com in self.FlatInstance.com_dict.values():
                line = {'id': com.id,
                        'origin': com.origin.id,
                        'destination': com.destination.id,
                        'demand': com.demand,
                        'release_time': com.release_time,
                        'deadline': com.deadline}
                if self.Parameters['DP']:
                    line['arc_list'] = com.arc_list
                    line['node_list'] = com.node_list
                csw.writerow(line)

    def write_parameters(self):
        output_file = self.folder + 'parameters.csv'
        w = csv.writer(open(output_file, "w"))
        w.writerow(['parameter_name', 'value'])
        Parameters = self.Parameters
        nec_Parameters = {'REGIONAL': Parameters['REGIONAL'], 'DP': Parameters['DP'],
                          'GROUP_TIMES': Parameters['GROUP_TIMES'],
                          'n': self.FlatInstance.n, 'm': self.FlatInstance.m, 'k': self.FlatInstance.k,
                          'h': self.FlatInstance.h, 'cost': self.FlatInstance.cost,
                          'capacity': self.FlatInstance.capacity, 'e_sigma_factor': self.e_sigma_factor,
                          'f_mean_factor': self.f_mean_factor, 'f_sigma_factor': self.f_sigma_factor,
                          'Delta': self.delta, 'num_fixed_times': self.num_fixed_times}
        for key, val in nec_Parameters.items():
            w.writerow([key, val])


