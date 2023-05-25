import csv
from os import path as file_path
import os


class OutputWriter:
    def __init__(self, Instance):
        self.Instance = Instance
        self.field_names = ['Test_id', 'arc_disc',
                            'DDD time', 'solved', 'gap',
                            'num_iterations',
                            'num_vars_final', 'num_constraints_final',
                            'n', 'm', 'k', 'h', 'REGIONAL', 'DP', 'GROUP_TIMES', 'cost', 'capacity',
                            'num_fixed_times', 'e_sigma_factor', 'f_mean_factor', 'f_sigma_factor',
                            'Delta',
                            'iteration_times',
                            'num_variables', 'num_constraints',
                            'DDD_value', 'iteration_LBs', 'iteration_UBs',
                            'iteration_V_S', 'final_V_S_size']
        self.write_data_summary()

    def write_data_summary(self):
        write_header = False
        for location in [self.Instance.input_folder, self.Instance.instance_folder]:
            output_file = file_path.join(location, 'testing_summary.csv')
            if not os.path.isfile(output_file):
                write_header = True
            with open(output_file, "a") as f_out:
                names = self.field_names
                csw = csv.DictWriter(f_out, names)
                if write_header:
                    csw.writeheader()
                line = self.__get_dict(self.Instance)
                csw.writerow(line)

    def __get_dict(self, Instance):
        line = {'Test_id': Instance.id,
                'arc_disc': Instance.scenario,
                'DDD time': Instance.DDD_time,
                'solved': Instance.solved,
                'gap': Instance.gap,

                'num_vars_final': Instance.num_variables[-1],
                'num_constraints_final': Instance.num_constraints[-1],
                'num_iterations': len(Instance.iteration_times),
                'final_V_S_size': len(Instance.final_V_S),

                'REGIONAL': Instance.Parameters['REGIONAL'],
                'DP': Instance.Parameters['DP'],
                'GROUP_TIMES': Instance.Parameters['GROUP_TIMES'],
                'n': Instance.Parameters['n'],
                'm': Instance.Parameters['m'],
                'k': Instance.Parameters['k'],
                'h': Instance.Parameters['h'],
                'cost': Instance.Parameters['cost'],
                'capacity': Instance.Parameters['capacity'],
                'e_sigma_factor': Instance.Parameters['e_sigma_factor'],
                'f_mean_factor': Instance.Parameters['f_mean_factor'],
                'f_sigma_factor': Instance.Parameters['f_sigma_factor'],
                'Delta': Instance.Parameters['Delta'],
                'num_fixed_times': Instance.Parameters['num_fixed_times'],

                'iteration_times': Instance.iteration_times,
                'DDD_value': Instance.DDD_value,
                'num_variables': Instance.num_variables,
                'num_constraints': Instance.num_constraints,
                'iteration_LBs': Instance.iteration_LBs,
                'iteration_UBs': Instance.iteration_UBs,
                'iteration_V_S': Instance.V_S_sizes
                }
        return line


