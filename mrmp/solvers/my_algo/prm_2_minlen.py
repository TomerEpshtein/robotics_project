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
import mrmp.conversions as conversions
from mrmp.solvers import sum_distances
from mrmp.solvers import bounding_box

from mrmp.solvers.my_algo import local_prm_discs

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
    except Exception as total_error_saved:
        print("argument is not an integer", file=writer)
        return path
    print("num_landmarks=", num_landmarks, file=writer)
    num_robots = len(robots)
    print("num_robots=", num_robots, file=writer)
    # for technical reasons related to the way the python bindings for this project were generated, we need
    # the condition "(dim / num_robots) >= 2" to hold
    if num_robots == 0:
        print("unsupported number of robots:", num_robots, file=writer)
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
    print('Sampling landmarks', file=writer)

    ######################
    # Sampling landmarks
    ######################
    for i in range(num_landmarks):
        if not isRunning[0]:
            print("Aborted", file=writer)
            return path, G

        p = sample_valid_landmark(min_x, max_x, min_y, max_y, collision_detectors, num_robots, radii)
        G.add_node(p)
        points.append(p)
        if i % 500 == 0:
            print(i, "landmarks sampled", file=writer)
    print(num_landmarks, "landmarks sampled", file=writer)

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
    print('Connecting landmarks', file=writer)
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
            print('Connected', i, 'landmarks to their nearest neighbors', file=writer)

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
        print("A path of length", sum(lengths), "was found", file=writer)
        for i in range(num_robots):
            print('Length traveled by robot', i, ":", lengths[i], file=writer)
        for p in temp:
            path.append(conversions.to_point_2_list(p, num_robots))
    else:
        print("No path was found", file=writer)

    """
    *** OUR CODE ***
    """
    print("*** RUNNING OUR IMPROVING CODE ***", file=writer)
    if len(path) < 3:
        return path, G

    # Trying to delete vertices to make the path smaller
    prev_length = 0
    new_length = -1
    new_path = path
    while new_length < prev_length:
        prev_length = len(new_path)
        new_path = remove_vertices_from_path(new_path, collision_detectors, num_robots, radii)
        new_length = len(new_path)

    CHUNK_SIZE = 4
    rounds = len(new_path) // CHUNK_SIZE + 1
    last_round_size = len(new_path) % CHUNK_SIZE
    if last_round_size == 0:
        last_round_size = CHUNK_SIZE
        rounds -= 1

    current_path_index = 0  # index which tells us where we are at the path
    final_path = []
    round_num = 0
    while round_num < rounds:
        # On each round we pass over a sub-path of path of length CHUNK_SIZE or less
        round_num += 1

        if round_num < rounds:
            current_sub_path = new_path[current_path_index:current_path_index+CHUNK_SIZE]
        else:
            # last round
            current_sub_path = new_path[current_path_index:current_path_index + last_round_size]

        if len(current_sub_path) == 1:
            final_path.append(current_sub_path[0])
            continue
        elif not current_sub_path:
            continue

        sub_path_length = calculate_length_from_start_to_end(current_sub_path)

        # improving only the first path
        first_fake_robot = {"center": current_sub_path[0][0], "radius": robots[0]["radius"]}
        second_fake_robot = {"center": current_sub_path[0][1], "radius": robots[1]["radius"]}

        src = conversions.to_point_d([current_sub_path[0][0], current_sub_path[0][1]])
        dst = conversions.to_point_d([current_sub_path[-1][0], current_sub_path[-1][1]])
        if edge_valid(collision_detectors,
                      src,
                      dst,
                      num_robots, radii):
            # just add the edge and continue to the next sub-path
            final_path.append(conversions.to_point_2_list(src, num_robots))
            final_path.append(conversions.to_point_2_list(dst, num_robots))
            current_path_index += CHUNK_SIZE
            continue
        # calling to our local prm
        best_path, _ = local_prm_discs.generate_path_disc(
            [first_fake_robot, second_fake_robot], obstacles, disc_obstacles,
            [current_sub_path[-1][0], current_sub_path[-1][1]], 100, writer, isRunning
        )

        if best_path == [] or calculate_length_from_start_to_end(best_path) >= sub_path_length:
            if round_num == rounds:
                # last round
                x = last_round_size
            else:
                x = CHUNK_SIZE
            for _ in range(x):
                final_path.append(new_path[current_path_index])
                current_path_index += 1
        else:
            for i in range(len(best_path)):
                final_path.append(best_path[i])

            current_path_index += CHUNK_SIZE

    # Trying to delete vertices to make the path smaller
    prev_length = 0
    new_length = -1
    while new_length < prev_length:
        prev_length = len(final_path)
        final_path = remove_vertices_from_path(final_path, collision_detectors, num_robots, radii)
        new_length = len(final_path)

    # now we have our final path, we will build the final graph
    final_G = nx.Graph()
    for i in range(len(final_path) - 1):
        final_G.add_node(conversions.to_point_d(final_path[i]))
        final_G.add_node(conversions.to_point_d(final_path[i+1]))
        final_G.add_edge(conversions.to_point_d(final_path[i]),
                         conversions.to_point_d(final_path[i+1]))

    final_path_length = calculate_length_from_start_to_end(final_path)
    origin_prm_path_length = calculate_length_from_start_to_end(path)
    error_saved = origin_prm_path_length - final_path_length

    print("*** RESULTS ***")
    print(f"final total length is {final_path_length}", file=writer)
    print(f"Saved {error_saved} of total path length regarding to the basic prm,"
          f" which are {error_saved/origin_prm_path_length * 100}%", file=writer)

    t1 = time.perf_counter()
    print("Time taken:", t1 - t0, "seconds", file=writer)

    return final_path, final_G


def remove_vertices_from_path(path, collision_detectors, num_robots, radii):
    faster_path = [path[0]]
    for i in range(0, len(path) - 2, 2):
        if edge_valid(collision_detectors, conversions.to_point_d(path[i]),
                      conversions.to_point_d(path[i + 2]),
                      num_robots, radii):
            pass
        else:
            faster_path.append(path[i + 1])
        faster_path.append(path[i + 2])

    if len(path) % 2 == 0:
        faster_path.append(path[-1])

    return faster_path


def calculate_length_from_start_to_end(path):
    path_length = 0
    for i in range(len(path) - 1):
        first_edge_length = math.sqrt(
            (path[i][0][0].to_double() - path[i + 1][0][0].to_double()) ** 2
            + (path[i][0][1].to_double() - path[i + 1][0][1].to_double()) ** 2
        )

        second_edge_length = math.sqrt(
            (path[i][1][0].to_double() - path[i + 1][1][0].to_double()) ** 2
            + (path[i][1][1].to_double() - path[i + 1][1][1].to_double()) ** 2
        )

        path_length += first_edge_length
        path_length += second_edge_length

    return path_length


# throughout the code, wherever we need to return a number of type double to CGAL,
# we convert it using FT() (which stands for field number type)
def point_d_to_arr(p: Point_d):
    return [p[i].to_double() for i in range(p.dimension())]


# find one free landmark (milestone) within the bounding box
def sample_valid_landmark(min_x, max_x, min_y, max_y, collision_detectors, num_robots, radii):
    while True:
        points = []
        # for each robot check that its configuration (point) is in the free space
        for i in range(num_robots):
            rand_x = FT(random.uniform(min_x, max_x))
            rand_y = FT(random.uniform(min_y, max_y))
            p = Point_2(rand_x, rand_y)
            if collision_detectors[i].is_point_valid(p):
                points.append(p)
            else:
                break
        # verify that the robots do not collide with one another at the sampled configuration
        if len(points) == num_robots and not collision_detection.check_intersection_static(points, radii):
            return conversions.to_point_d(points)


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
