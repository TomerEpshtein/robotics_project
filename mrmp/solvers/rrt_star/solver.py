from datetime import datetime

from bindings import *
from geometry_utils import collision_detection
from mrmp.conversions import to_point_2_list
from mrmp.solvers.my_algo.prm_2_minlen import calculate_length_from_start_to_end
from mrmp.solvers.rrt_star.nearest_point_search import NearestPointSearch
from mrmp.solvers.rrt_star.random_points_in_polygon_generator import PointsGenerator
from mrmp.solvers.rrt_star.rrt_star import RrtStar

STEP_SIZE_VALUE = 1
STEP_SIZE = FT(Gmpq(STEP_SIZE_VALUE))
NUM_SAMPLES = 1000


def _get_total_distance(path, num_robots):
    # divide the path to point_2_list in each element instead point_d
    path_divided = [to_point_2_list(p, num_robots) for p in path]
    return calculate_length_from_start_to_end(path_divided)


def generate_path_disc(robots, obstacles, disc_obstacles, destinations, argument, writer, isRunning):
    start_time = datetime.now()
    print(f"start time {start_time}", file=writer)

    path = []
    try:
        num_samples = int(argument) if argument != "" else NUM_SAMPLES
    except Exception:
        print("argument is not an integer", file=writer)
        return path

    num_robots = len(robots)
    radii = [robot['radius'] for robot in robots]
    collision_detectors = [collision_detection.Collision_detector(obstacles, disc_obstacles, radius) for radius in
                           radii]

    center_points = [robot['center'] for robot in robots]
    nearest_point_search = NearestPointSearch([])
    points_generator = PointsGenerator(obstacles, num_robots, radii, collision_detectors)
    rrt = RrtStar(STEP_SIZE, points_generator, num_samples, nearest_point_search,
                  collision_detectors, num_robots, radii)

    generated_path = None
    while generated_path is None:
        if not isRunning[0]:
            print("Aborted", file=writer)
            return path, rrt.graph

        generated_path = rrt.get_path(center_points, destinations)
        if generated_path is not None:
            for p in generated_path:
                path.append(to_point_2_list(p, num_robots))
            print(_get_total_distance(generated_path, num_robots), file=writer)

    print(f"total time {datetime.now() - start_time}", file=writer)

    return path, rrt.graph
