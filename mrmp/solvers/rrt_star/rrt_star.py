import networkx as nx
import numpy as np

from bindings import FT, Point_d, Segment_2
from geometry_utils import collision_detection
from mrmp import conversions


class RrtStar:

    def __init__(self, step_size, random_points_generator, num_samples, nearest_point_search,
                 collision_detectors, num_robots, radii):
        self.num_robots = num_robots
        self.radii = radii
        self.collision_detectors = collision_detectors
        self.num_samples = num_samples
        self.random_points_generator = random_points_generator
        self.step_size = step_size
        self.nearest_point_search = nearest_point_search
        self.graph = nx.Graph()
        self.cost = dict()
        self.parents = dict()

    def _steer(self, rand, near, distance):
        if distance < self.step_size:
            return rand, distance
        dim = rand.dimension()

        def _get_masked_rand_point(is_rand=True):
            if is_rand:
                rand_shit = list(map(lambda item: bool(item), list(np.random.rand(dim) < 0.7)))
            else:
                # all True
                rand_shit = list(map(lambda item: bool(item), list(np.random.rand(dim) < 2)))

            local_rand_values = [rand[i] if rand_shit[i] is True else near[i] for i in range(dim)]
            return local_rand_values

        rand_values = _get_masked_rand_point()
        near_values = [near[i] for i in range(dim)]
        t = self.step_size / distance
        steer_values = [(FT(1) - t) * FT(near_values[i]) + t * FT(rand_values[i]) for i in range(dim)]
        steer_point = Point_d(dim, steer_values)
        return steer_point, self.nearest_point_search.get_distance(steer_point, near)

    def get_path(self, start, end):
        """
        :return: will return a path if succeeded within self.num_samples - None otherwise. An afterwards call to this
        function will try to generate a path based on previous samples along with new samples
        """
        start_point_d = self._initialize_start_point_data(start)
        destination_point_d = conversions.to_point_d(end)

        i = 0
        while i < self.num_samples:
            if destination_point_d in self.graph:
                break
            x_rand = self.random_points_generator.generate()
            x_near, distance = self.nearest_point_search.get_closest_point(x_rand)
            x_new, steer_distance = self._steer(x_rand, x_near, FT(float(distance)))
            if x_new not in self.graph:
                if self.edge_valid(x_near, x_new):
                    x_near_neighbors = self.nearest_point_search.get_neighborhood(x_new)
                    self._add_vertex(x_new)
                    i += 1
                    if i % 100 == 0:
                        print(f"added {i} nodes")
                    x_min = x_near
                    c_min = self.cost[x_near] + steer_distance
                    for x_near in x_near_neighbors:
                        if self.edge_valid(x_near, x_new):
                            if self.cost[x_near] + self.nearest_point_search.get_distance(x_near, x_new) < c_min:
                                c_min = self.cost[x_near] + self.nearest_point_search.get_distance(x_near, x_new)
                                x_min = x_near

                    self.graph.add_edge(x_min, x_new)
                    self.parents[x_new] = x_min
                    self.cost[x_new] = c_min

                    for x_near in x_near_neighbors:
                        if self.edge_valid(x_near, x_new):
                            if self.cost[x_new] + self.nearest_point_search.get_distance(x_near, x_new) < self.cost[x_near]:
                                self._update_edges_of_x_near(x_near, x_new)

                    # check if the new point is connected to destinations
                    if self.edge_valid(x_new, destination_point_d):
                        self.graph.add_edge(x_new, destination_point_d)
                        self.parents[destination_point_d] = x_new
                        self.cost[destination_point_d] = self.cost[x_new] + self.nearest_point_search.get_distance(
                            destination_point_d, x_new
                        )
                        print("Finish")

        if destination_point_d in self.graph:
            has_path = nx.has_path(self.graph, start_point_d, destination_point_d)
            if has_path:
                return nx.shortest_path(self.graph, start_point_d, destination_point_d)
            else:
                return None

    def _initialize_start_point_data(self, start):
        start_point_d = conversions.to_point_d(start)
        self._add_vertex(start_point_d)
        self.parents[start_point_d] = None
        self.cost[start_point_d] = FT(0)
        return start_point_d

    def _update_edges_of_x_near(self, x_near, x_new):
        x_parent = self.parents[x_near]
        self.graph.remove_edge(x_parent, x_near)
        self.graph.add_edge(x_new, x_near)
        self.parents[x_near] = x_new
        self.cost[x_near] = self.cost[x_new] + self.nearest_point_search.get_distance(x_new, x_near)

    def _add_vertex(self, steer_point):
        self.graph.add_nodes_from([steer_point])
        self.nearest_point_search.add_point(steer_point)

    # check whether the edge pq is collision free
    # the collision detection module sits on top of CGAL arrangements
    def edge_valid(self, p: Point_d, q: Point_d):
        p = conversions.to_point_2_list(p, self.num_robots)
        q = conversions.to_point_2_list(q, self.num_robots)
        edges = []
        # for each robot check that its path (line segment) is in the free space
        for i in range(self.num_robots):
            edge = Segment_2(p[i], q[i])
            if not self.collision_detectors[i].is_edge_valid(edge):
                return False
            edges.append(edge)
        # verify that the robots do not collide with one another along the C-space edge
        if collision_detection.check_intersection_against_robots(edges, self.radii):
            return False
        return True
