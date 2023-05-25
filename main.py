import sys
import os

sys.path.append(os.getcwd() + "/Applications")
sys.path.append(os.getcwd() + "/Objects")

from InstanceGenerator import InstanceGen
from InstanceSolver import SolveInstance
from OutputWriter import OutputWriter

instance_dict = {'GROUP_TIMES': 'critical_times', 'DP': 'designated_paths', 'REGIONAL': 'hub_and_spoke'}
# Options:
# process: 'run_instances', 'gen_instances'
# family: 'REGIONAL', 'DP', 'GROUP_TIMES'


def run_DDD(process='run_instances', family='REGIONAL', folder=None):
    if folder is None:
        folder = '/Instances/' + instance_dict[family] + '/'
    solve_Parameters = {'INSTANCE_FOLDER': folder, 'DP': False, 'REGIONAL': False, 'GROUP_TIMES': False, family: True,
                        'TIME_LIMIT': 10800, 'OPTIMALITY_GAP': 0.01}
    if process == 'gen_instances':
        InstanceGen(solve_Parameters)
    elif process == 'run_instances':
        directory = os.getcwd() + folder
        input_folder = directory
        print('directory:', directory)
        for flat_instance in next(os.walk(directory))[1]:
            print('flat instance:', flat_instance)
            sub_directory = directory + flat_instance + '/'
            for SND_instance in next(os.walk(sub_directory))[1]:
                for scenario in ['arc_disc', 'node_disc']:
                    instance_folder = sub_directory + SND_instance + '/'
                    instance_id = flat_instance + '-' + SND_instance
                    run_instance(solve_Parameters, input_folder, instance_folder, instance_id, scenario)


def run_instance(solve_Parameters, input_folder, instance_folder, instance_id, scenario):
    Instance = SolveInstance(solve_Parameters, input_folder, instance_folder, instance_id, scenario)
    OutputWriter(Instance)


def main():
    run_DDD()

main()
