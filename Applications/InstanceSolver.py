import time
import math
from gurobipy import GRB
from InputReader import InputReader
from AuxiliaryNetworkGenerator import AuxiliaryNetwork
from TimedNodeGenerator import GenerateTimedNodes
from TimedArcGenerator import TimedArcGenerator
from SetGenerator import SetGenerator
from SND_IP import SNDSolver
from UpperBound import UpperBound
from Refinement import RefineDiscretization


class SolveInstance:
    def __init__(self, solve_Parameters, input_folder, instance_folder, SND_instance, scenario):
        self.instance_folder = instance_folder
        self.solve_Parameters = solve_Parameters
        self.input_folder = input_folder
        self.SND_instance = SND_instance
        self.scenario = scenario

        # Initializing DDD
        self.__initialize_DDD_data()
        self.V_S = self.__initialize_DDD()
        start_time = time.time()
        while self.gap > solve_Parameters['OPTIMALITY_GAP']:

            # Lower bound
            time_limit = solve_Parameters['TIME_LIMIT'] - (time.time() - start_time)
            G_S, D_S = self.__generate_timed_data(self.V_S)
            self.IP_S = SNDSolver(self.Input_data, G_S, D_S, time_limit)
            if self.IP_S.model.status == GRB.TIME_LIMIT:
                self.__update_iteration_data()
                self.solved = False
                break

            # Upper bound
            self.LP_UB = UpperBound(self.Input_data, G_S, self.IP_S)
            self.UB = min(self.UB, self.LP_UB.UB)

            # Refinement step
            refinement = RefineDiscretization(self.Input_data, G_S, self.LP_UB)
            self.V_S = refinement.V_S_new

            # Recording iteration data
            self.__update_iteration_data()
            if self.LP_UB.is_feasible:
                break
            if time.time() - start_time > solve_Parameters['TIME_LIMIT']:
                self.solved = False
                break

        # Recording final iteration data
        self.__record_final_data()
        print('at end of algorithm:', self.num_variables)

    def __initialize_DDD_data(self):
        self.id = self.SND_instance
        self.solved = True
        self.DDD_start_time = time.time()
        self.iteration_start_time = time.time()
        self.LB = 0
        self.UB = math.inf
        self.gap = 1
        self.iteration = 0
        self.iteration_times = []
        self.num_variables = []
        self.num_constraints = []
        self.iteration_LBs = []
        self.iteration_UBs = []
        self.iteration_gaps = []
        self.V_S_sizes = []

    def __initialize_DDD(self):
        self.Input_data = InputReader(self.instance_folder)
        self.Parameters = self.Input_data.Parameters
        # Creating arc partition and auxiliary graph
        self.auxiliary_network = AuxiliaryNetwork(self.Input_data, self.Parameters)
        # Generating the initial timed (auxiliary) nodes V_S
        timed_nodes = GenerateTimedNodes(self.Input_data, self.auxiliary_network)
        V_S = timed_nodes.V_S
        return V_S

    def __generate_timed_data(self, V_S):
        timed_arc_data = TimedArcGenerator(self.solve_Parameters, self.Input_data, self.auxiliary_network, V_S, self.scenario)
        G_S, D_S = timed_arc_data.G_S, timed_arc_data.D_S
        SetGenerator(self.Input_data, G_S, D_S)
        return G_S, D_S

    def __update_iteration_data(self):
        self.iteration += 1
        self.LB = max(self.IP_S.obj_val, self.LB)
        self.iteration_LBs.append(round(self.LB, 2))
        self.V_S_sizes.append(len(self.V_S))
        self.iteration_UBs.append(round(self.UB, 2))
        self.iteration_gaps.append(round((self.UB - self.LB) / self.LB, 2))
        self.iteration_times.append(round(time.time() - self.iteration_start_time, 2))
        self.iteration_start_time = time.time()
        self.num_constraints.append(self.IP_S.num_constraints)
        self.num_variables.append(self.IP_S.num_vars)
        if self.UB != math.inf:
            self.gap = (self.UB - self.LB) / self.UB
        self.__print_iteration_data_short()

    def __record_final_data(self):
        self.DDD_time = round(time.time() - self.DDD_start_time, 2)
        self.DDD_value = round(self.UB, 2)
        self.final_V_S = self.V_S
        self.num_constraints_final = self.IP_S.num_constraints
        self.num_vars_final = self.IP_S.num_vars
        self.num_iterations = self.iteration

    def __print_iteration_data_short(self):
        print('\n-----Iteration ' + str(self.iteration) + '-----')
        print('LB is:', round(self.LB, 1))
        print('UB is:', round(self.UB, 1))
        print('gap is:', round(self.gap, 2))
        print('iteration times:', self.iteration_times)
        print('total time:', round(time.time() - self.DDD_start_time, 2))








