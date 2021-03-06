import os.path
import sys

sys.path.insert(0, os.path.dirname(__file__))

import sklearn.neighbors
import numpy as np
from bindings import *
from geometry_utils import collision_detection
import networkx as nx
import random
import time
import math
from mrmp import conversions
from mrmp.solvers import sum_distances
from mrmp.solvers import bounding_box

# Number of nearest neighbors to search for in the k-d tree
K = 15


# generate_path() is our main PRM function
# it constructs a PRM (probabilistic roadmap)
# and searches in it for a path from start (robots) to target (destinations)
def generate_path_disc(robots, obstacles, disc_obstacles, destinations, argument, writer, isRunning):
    ###################
    # Preperations
    ###################
    t0 = time.perf_counter()
    path = []
    try:
        num_landmarks = int(argument)
    except Exception as e:
        print("argument is not an integer", file=writer)
        return path
    print("num_landmarks=", num_landmarks)
    num_robots = len(robots)
    print("num_robots=", num_robots)
    # for technical reasons related to the way the python bindings for this project were generated, we need
    # the condition "(dim / num_robots) >= 2" to hold
    if num_robots == 0:
        print("unsupported number of robots:", num_robots)
        return path
    # compute the free C-space of a single robot by expanding the obstacles by the disc robot radius
    # and maintaining a representation of the complement of the expanded obstacles
    sources = [robot['center'] for robot in robots]
    radii = [robot['radius'] for robot in robots]
    collision_detectors = [collision_detection.Collision_detector(obstacles, disc_obstacles, radius) for radius in
                           radii]
    min_x, max_x, min_y, max_y = bounding_box.calc_bbox(obstacles, sources, destinations, max(radii))

    # turn the start position of the robots (the array robots) into a d-dim point, d = 2 * num_robots
    sources = conversions.to_point_d(sources)
    # turn the target position of the robots (the array destinations) into a d-dim point, d = 2 * num_robots
    destinations = conversions.to_point_d(destinations)
    # we use the networkx Python package to define and manipulate graphs
    # G is an undirected graph, which will represent the PRM
    G = nx.Graph()
    points = [sources, destinations]
    # we also add these two configurations as nodes to the PRM G
    G.add_nodes_from([sources, destinations])
    print('Sampling landmarks')

    ######################
    # Sampling landmarks
    ######################
    for i in range(num_landmarks):
        if not isRunning[0]:
            print("Aborted", file=writer)
            return path, G

        p = sample_valid_landmark(min_x, max_x, min_y, max_y, collision_detectors, num_robots, radii,
                                  robots[0]['center'], robots[1]['center'], destinations)
        G.add_node(p)
        points.append(p)
        if i % 500 == 0:
            print(i, "landmarks sampled")
    print(num_landmarks, "landmarks sampled")

    ### !!!
    # Distnace functions
    ### !!!
    distance = sum_distances.sum_distances(num_robots)
    custom_dist = sum_distances.numpy_sum_distance_for_n(num_robots)

    _points = np.array([point_d_to_arr(p) for p in points])

    ########################
    # Constract the roadmap
    ########################
    # User defined metric cannot be used with the kd_tree algorithm
    kdt = sklearn.neighbors.NearestNeighbors(n_neighbors=K, metric=custom_dist, algorithm='auto')
    # kdt = sklearn.neighbors.NearestNeighbors(n_neighbors=K, algorithm='kd_tree')
    kdt.fit(_points)
    print('Connecting landmarks')
    for i in range(len(points)):
        if not isRunning[0]:
            print("Aborted", file=writer)
            return path, G

        p = points[i]
        k_neighbors = kdt.kneighbors([_points[i]], return_distance=False)

        if edge_valid(collision_detectors, p, destinations, num_robots, radii):
            d = distance.transformed_distance(p, destinations).to_double()
            G.add_edge(p, destinations, weight=d)
        for j in k_neighbors[0]:
            neighbor = points[j]
            if not G.has_edge(p, neighbor):
                # check if we can add an edge to the graph
                if edge_valid(collision_detectors, p, neighbor, num_robots, radii):
                    d = distance.transformed_distance(p, neighbor).to_double()
                    G.add_edge(p, neighbor, weight=d)
        if i % 500 == 0:
            print('Connected', i, 'landmarks to their nearest neighbors')

    ########################
    # Finding a valid path
    ########################
    if nx.has_path(G, sources, destinations):
        temp = nx.dijkstra_path(G, sources, destinations, weight='weight')
        lengths = [0 for _ in range(num_robots)]
        if len(temp) > 1:
            for i in range(len(temp) - 1):
                p = temp[i]
                q = temp[i + 1]
                for j in range(num_robots):
                    dx = p[2 * j].to_double() - q[2 * j].to_double()
                    dy = p[2 * j + 1].to_double() - q[2 * j + 1].to_double()
                    lengths[j] += math.sqrt((dx * dx + dy * dy))
        print("A path of length", sum(lengths), "was found")
        for i in range(num_robots):
            print('Length traveled by robot', i, ":", lengths[i])
        for p in temp:
            path.append(conversions.to_point_2_list(p, num_robots))
    else:
        print("No path was found")
    t1 = time.perf_counter()
    print("Time taken:", t1 - t0, "seconds")
    return path, G


# throughout the code, wherever we need to return a number of type double to CGAL,
# we convert it using FT() (which stands for field number type)
def point_d_to_arr(p: Point_d):
    return [p[i].to_double() for i in range(p.dimension())]


# find one free landmark (milestone) within the bounding box
def sample_valid_landmark(min_x, max_x, min_y, max_y, collision_detectors, num_robots, radii, first_robot, second_robot,
                          destinations):
    first_distance = distance(first_robot, Point_2(point_d_to_arr(destinations)[0], point_d_to_arr(destinations)[1]))
    second_distance = distance(second_robot, Point_2(point_d_to_arr(destinations)[2], point_d_to_arr(destinations)[3]))
    while True:
        points = []
        # for each robot check that its configuration (point) is in the free space
        for i in range(num_robots):
            rand_x = FT(random.uniform(min_x, max_x))
            rand_y = FT(random.uniform(min_y, max_y))
            p = Point_2(rand_x, rand_y)
            if collision_detectors[i].is_point_valid(p) and (distance(first_robot, p) < first_distance
                                                             or distance(second_robot, p) < second_distance):
                points.append(p)
            else:
                break
        # verify that the robots do not collide with one another at the sampled configuration
        if len(points) == num_robots and not collision_detection.check_intersection_static(points, radii):
            return conversions.to_point_d(points)


def distance(first, second):
    return math.sqrt((second[0].to_double() - first[0].to_double()) ** 2 + (
                    second[1].to_double() - first[1].to_double()) ** 2)


# check whether the edge pq is collision free
# the collision detection module sits on top of CGAL arrangements
def edge_valid(collision_detectors, p: Point_d, q: Point_d, num_robots, radii):
    p = conversions.to_point_2_list(p, num_robots)
    q = conversions.to_point_2_list(q, num_robots)
    edges = []
    # for each robot check that its path (line segment) is in the free space
    for i in range(num_robots):
        edge = Segment_2(p[i], q[i])
        if not collision_detectors[i].is_edge_valid(edge):
            return False
        edges.append(edge)
    # verify that the robots do not collide with one another along the C-space edge
    if collision_detection.check_intersection_against_robots(edges, radii):
        return False
    return True
