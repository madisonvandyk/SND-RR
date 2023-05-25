class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.outgoing_arcs = {}
        self.node_in_D = 0

        self.dist_to_node = {}
        self.values = set()
        self.node_copies = {}
        self.parts = set()
        self.num = 0

        # fields only used for region-based networks
        self.x = 0
        self.y = 0
        self.hub = False
        self.region_size = 0
        self.region_hub = None

        # for instance generation
        self.release_times = []
        self.deadlines = []

        # for efficiency of generating sets
        self.timed_copies = {}

    def add_outgoing_arc(self, arc):
        self.outgoing_arcs[arc.id] = arc

    def add_node_copy(self, node_copy):
        self.node_copies[node_copy.id] = node_copy

    def set_node_in_D(self, node_in_D):
        self.node_in_D = node_in_D
