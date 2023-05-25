class TimedArc:
    def __init__(self, arc, time, V_S, red_time):
        self.id = str(arc.id) + '_' + str(time)
        self.base_arc = arc
        self.base_id = arc.id
        # origin and destination are now relative to N_T, not to the original nodes.
        self.origin_id = arc.origin_id
        self.destination_id = arc.destination_id
        self.origin = V_S[(arc.origin_id, time)]
        self.destination = V_S[(arc.destination_id, time + red_time)]
        self.time = time
        self.transit_time = arc.transit_time
        self.capacity = arc.capacity
        self.fixed_cost = arc.fixed_cost
        self.variable_cost = arc.variable_cost
        self.red_time = red_time
        self.paths = {}
        self.commodities = {}

        # arc-based discretization
        self.projected_set = {}
        self.project_to_D_S = 0

        # from support
        self.K_in_support = {}
        self.K_pairs = []
        self.demand = 0


