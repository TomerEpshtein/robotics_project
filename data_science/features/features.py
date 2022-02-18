"""
A script to extract features of: total obstacles area, robots distances + manually I added
the features: maximum distance required for one of the robots to pass to its destination
and 0/1/2 number of robots where can move linearly at the beginning to their destination
"""
import csv
import json
import math
import os
import pathlib

COLUMNS = ["scene_name", "total_obstacles_area", "robots_distances"]


def calculate_total_area_of_polygonals(obstacles):
    total_size = 0
    for obstacle in obstacles:
        total_size += calculate_area_polygonal_obstacle(obstacle)

    return total_size


def calculate_total_area_of_discs(disc_obstacles):
    total_size = 0
    for obstacle in disc_obstacles:
        total_size += math.pi * (obstacle["radius"] ** 2)
    return total_size


def calculate_area_polygonal_obstacle(obstacle):
    """
    Assuming in obstacle all the points are ordered clockwise or counterclockwise
    """
    # Extract all X's and all Y's of the polygons' points
    X = []
    Y = []
    for point in obstacle:
        X.append(point[0])
        Y.append(point[1])

    # Calculate value of shoelace formula
    n = len(X)
    area = 0.0
    j = n - 1
    for i in range(0, n):
        area += (X[j] + X[i]) * (Y[j] - Y[i])
        j = i  # j is previous vertex to i

    return int(abs(area / 2.0))


def calculate_total_area_of_obstacles(scene_path):
    """
    Given a scene path, calculate its total area of obstacles

    note: Assuming obstacles don't intersect each one + each obstacle is a polygon.
    """
    # Extract a list of all the obstacles
    with open(scene_path) as file_descriptor:
        scene_data = json.load(file_descriptor)
        polygonal_obstacles = scene_data["obstacles"]
        disc_obstacles = scene_data["disc_obstacles"]
    return calculate_total_area_of_polygonals(polygonal_obstacles) + calculate_total_area_of_discs(disc_obstacles)


def calculate_robots_distances(scene_path):
    with open(scene_path) as file_descriptor:
        scene_data = json.load(file_descriptor)
        sources, targets = scene_data["sources"], scene_data["targets"]
        first_distance = dist_2_points(sources[0], targets[0])
        second_distance = dist_2_points(sources[1], targets[1])

    return first_distance + second_distance


def dist_2_points(first, second):
    return math.sqrt((first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2)


working_directory = pathlib.Path(__file__).parent.parent.parent.resolve().__str__()
SCENES_PATHS = [f"{i}.json" for i in range(1, 101)]
rows = []
for scene_name in SCENES_PATHS:
    row = {"scene_name": f"{scene_name}"}
    path = os.path.join(working_directory, "mrmp", "scenes", scene_name)
    total_area_of_obstacles = calculate_total_area_of_obstacles(path)
    row["total_obstacles_area"] = total_area_of_obstacles
    row["robots_distances"] = calculate_robots_distances(path)
    rows.append(row)

with open('results.csv', 'w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
