import os
import pathlib
import time
import json
from bindings import *
from mrmp.solvers.my_algo.prm_2_minlen import calculate_length_from_start_to_end

working_directory = pathlib.Path(__file__).parent.parent.parent.resolve().__str__()
mrmp_headless_path = os.path.join(working_directory, "mrmp", "mrmp_headless.py")

SCENES_PATHS = [f"{i}.json" for i in range(1, 101)]
BASE_COMMAND_TO_RUN = "python {mrmp_headless} --scene={scene} --solver={solver}"

rows = []
time_rows = []
for scene_name in SCENES_PATHS:
    row = {"scene_name": f"{scene_name}"}
    print('\x1b[6;31;32m' + scene_name + '\x1b[0m')
    scene_path = os.path.join(working_directory, "mrmp", "scenes", scene_name)

    num_landmarks = 300
    base_command_to_run = BASE_COMMAND_TO_RUN.format(mrmp_headless=mrmp_headless_path,
                                                scene=scene_path,
                                                solver=os.path.join(working_directory, "mrmp", "solvers",
                                                                    "prm_discs.py"))

    my_quality = 0
    time_to_run = 0
    lengths = []
    qualities = []
    for _ in range(10):
        inner_stop = False
        while not inner_stop:
            command_to_run = base_command_to_run + f" --argument={num_landmarks}"
            print(f"Running the command:\n {command_to_run}")
            a0 = time.time()
            c = os.popen(command_to_run).read()
            a1 = time.time()
            output_rows = c.split("\n")
            if output_rows[-2] == "Valid motion":
                inner_stop = True
                path = output_rows[-3]
                path = json.loads(path)
                lengths.append(len(path))
                same_path = [[Point_2(p[0], p[1]), Point_2(p[2], p[3])] for p in path]
                qualities.append(calculate_length_from_start_to_end(same_path))
            else:
                num_landmarks = 2 * num_landmarks
                continue

    row["length"] = sum(lengths)/10
    row["quality"] = sum(qualities)/10

    rows.append(row)

for r in rows:
    print(r)
