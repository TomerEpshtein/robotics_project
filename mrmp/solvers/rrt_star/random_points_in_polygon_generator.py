import random

import numpy as np
from bindings import Point_d, FT, Point_2
from geometry_utils import collision_detection
from mrmp import conversions


class PointsGenerator:
    def __init__(self, obstacles, num_robots, radii, collision_detectors):
        self.num_robots = num_robots
        self.radii = radii
        self.collision_detectors = collision_detectors
        self.obstacles = obstacles
        self.positions_lambdas = [lambda p: p.x(), lambda p: p.y()]
        self.min_x = self._get_extreme(0, min_flag=True)
        self.max_x = self._get_extreme(0)
        self.min_y = self._get_extreme(1, min_flag=True)
        self.max_y = self._get_extreme(1)

    def _get_extreme(self, position, min_flag=False):
        """
        Get min/max value of x/y axis - from all the obstacles at self.obstacles
        """
        coordinate_position_func = self.positions_lambdas[position]

        def calc_max_per_obstacle(obstacle, min_flag):
            points = [obstacle[i] for i in range(obstacle.size())]
            return max([coordinate_position_func(p) for p in points]) if not min_flag else\
                min([coordinate_position_func(p) for p in points])

        return max([calc_max_per_obstacle(obstacle, min_flag) for obstacle in self.obstacles]) if not min_flag else\
            min([calc_max_per_obstacle(obstacle, min_flag) for obstacle in self.obstacles])

    def generate(self):
        while True:
            points = []
            # for each robot check that its configuration (point) is in the free space
            for i in range(self.num_robots):
                rand_x = FT(random.uniform(self.min_x.to_double(), self.max_x.to_double()))
                rand_y = FT(random.uniform(self.min_y.to_double(), self.max_y.to_double()))
                p = Point_2(rand_x, rand_y)
                if self.collision_detectors[i].is_point_valid(p):
                    points.append(p)
                else:
                    break
            # verify that the robots do not collide with one another at the sampled configuration
            if len(points) == self.num_robots and not collision_detection.check_intersection_static(points, self.radii):
                return conversions.to_point_d(points)
