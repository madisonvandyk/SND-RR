class TimedNode:
    def __init__(self, node, time):
        self.base_node = node
        self.id = str(node.id) + '_' + str(time)
        self.base_id = node.id
        self.time = time
        self.in_timed_arcs = {}
        self.out_timed_arcs = {}

