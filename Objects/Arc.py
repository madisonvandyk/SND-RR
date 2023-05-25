class Arc:
    def __init__(self, arc_data, node_dict):
        self.id = arc_data.id
        self.origin_id = arc_data.origin
        self.destination_id = arc_data.destination
        self.origin = node_dict[self.origin_id]
        self.destination = node_dict[self.destination_id]
        self.fixed_cost = arc_data.fixed_cost
        self.variable_cost = {}
        self.sum_variable_costs = 0
        self.capacity = arc_data.capacity
        self.transit_time = arc_data.transit_time
        self.commodities_in_support = {}
        self.arc_copies = {}

        # partitioning
        self.part_num = 0
        self.arc_in_D = 0

        # speed up set generation
        self.timed_copies = {}

    def assign_var_costs(self, variable_costs):
        self.variable_cost = variable_costs
        self.sum_variable_costs = sum(self.variable_cost.values())

    def add_arc_copy(self, arc_copy):
        self.arc_copies[arc_copy.id] = arc_copy

    def set_arc_in_D(self, arc_in_D):
        self.arc_in_D = arc_in_D

