import math

import numpy as np
import sklearn.neighbors

from bindings import *


class NearestPointSearch:

    def __init__(self, num_robots, radius=FT(3)):
        self.radius = radius
        self.num_robots = num_robots
        self.custom_dist = numpy_sum_distance_for_n(num_robots)
        self.mapping = []

    def get_closest_point(self, point):
        """
        Returns the closes node to point by the self.custom_dict metric
        """
        kdt = sklearn.neighbors.NearestNeighbors(n_neighbors=1, metric=self.custom_dist, algorithm='auto')
        _points_nd = np.array([p[0] for p in self.mapping])
        kdt.fit(_points_nd)
        dist, k_neighbors = kdt.kneighbors([self.point_d_to_arr(point, 2 * self.num_robots)])
        index_of_closest_point = k_neighbors[0][0]
        # return the closest point as (Point_d, the distance)
        return self.mapping[index_of_closest_point][1], dist[0][0]

    def get_distance(self, p1, p2):
        if type(p1) == Point_d:
            p1 = self.point_d_to_arr(p1, 2 * self.num_robots)
        if type(p2) == Point_d:
            p2 = self.point_d_to_arr(p2, 2 * self.num_robots)

        return FT(self.custom_dist(p1, p2))

    def get_neighborhood(self, point):
        """
        Returns all the points which are in the distance of self.radius from point
        """
        _points_nd = np.array([p[0] for p in self.mapping])
        euclid_dist_func = numpy_sum_distance_for_n(self.num_robots, euclid=True)
        return [self.mapping[i][1] for i in range(len(_points_nd))
                if euclid_dist_func(_points_nd[i], np.array(self.point_d_to_arr(point, 2 * self.num_robots)))
                < self.radius.to_double()]

    def add_point(self, point):
        """
        Adding a new point as pair of two representations of it: by np array and by Point_d
        """
        point_nd = np.array(self.point_d_to_arr(point, 2 * self.num_robots))
        self.mapping.append([point_nd, point])

    @staticmethod
    def point_d_to_arr(p: Point_d, d):
        """
        Converts Point_d to array
        """
        return [p[i].to_double() for i in range(d)]


def numpy_sum_distance_for_n(n, euclid=False):
    def path_distance(p, q):
        sum_of_distances = 0
        for i in range(n):
            dx = p[2 * i] - q[2 * i]
            dy = p[2 * i + 1] - q[2 * i + 1]
            sum_of_distances += math.sqrt(dx * dx + dy * dy)
        return sum_of_distances

    def euclid_distance(p, q):
        s = 0
        for i in range(2*n):
            dx = p[i] - q[i]
            s += dx * dx
        return math.sqrt(s)

    return euclid_distance if euclid else path_distance
