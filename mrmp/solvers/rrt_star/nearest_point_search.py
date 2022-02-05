import math

from bindings import *


class NearestPointSearch:

    def __init__(self, initial_points, num_closest=1, epsilon=FT(Gmpq(0)), radius=FT(7), num_max_neighborhood=10):
        self.num_max_neighborhood = num_max_neighborhood
        self.radius = radius
        self.initial_points = initial_points
        self.epsilon = epsilon
        self.k = num_closest
        self.tree = Kd_tree(self.initial_points)
        self.small_tree = Kd_tree([])
        self.small_tree_num_points = 0
        self.points = set(initial_points)

    def get_closest_point(self, point):
        search = K_neighbor_search(self.tree, point, self.k, self.epsilon, True, Euclidean_distance(),
                                   True)
        closest_points = []
        search.k_neighbors(closest_points)

        small_search = K_neighbor_search(self.small_tree, point, self.k, self.epsilon, True, Euclidean_distance(),
                                         True)
        small_closest_points = []
        small_search.k_neighbors(small_closest_points)
        if closest_points == [] or (self.small_tree_num_points != 0 and small_closest_points[0][1] < closest_points[0][1]):
            return small_closest_points[0][0], small_closest_points[0][1].to_double()**0.5
        else:
            return closest_points[0][0], closest_points[0][1].to_double()**0.5

    def get_distance(self, p1, p2):
        tree = Kd_tree([p1])
        search = K_neighbor_search(tree, p2, 1, self.epsilon, True, Euclidean_distance(),
                                   True)
        closest_points = []
        search.k_neighbors(closest_points)
        _, squared_distance = closest_points[0]
        distance = FT(squared_distance.to_double() ** 0.5)
        return distance

    def get_neighborhood(self, point):
        search = K_neighbor_search(self.tree, point, self.num_max_neighborhood, self.epsilon, True,
                                   Euclidean_distance(),
                                   True)
        closest_points = []
        search.k_neighbors(closest_points)
        closest_points = [c_point for c_point in closest_points if c_point[1] < self.radius * self.radius]
        if self.small_tree_num_points == 0:
            return closest_points
        small_closest_points = []
        small_search = K_neighbor_search(self.small_tree, point, self.num_max_neighborhood, self.epsilon, True,
                                         Euclidean_distance(),
                                         True)
        small_search.k_neighbors(small_closest_points)
        small_closest_points = [c_point for c_point in small_closest_points if c_point[1] < self.radius * self.radius]

        def _merge(arr, arr2):
            points = arr + arr2
            points.sort(key=lambda item: item[1])
            return points[:self.num_max_neighborhood]

        closest_points = _merge(closest_points, small_closest_points)
        return closest_points

    def add_point(self, point):
        """
        :param point: Point_2
        :return: does not return
        """
        if point not in self.points:
            self.points.add(point)
            self.small_tree.insert(point)
            self.small_tree_num_points += 1
            if len(self.points) % 100 == 0:
                self.tree = Kd_tree(list(self.points))
                self.small_tree = Kd_tree([])
                self.small_tree_num_points = 0
