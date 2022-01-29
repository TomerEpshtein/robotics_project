import os
import pathlib
import pandas as pd

working_directory = pathlib.Path(__file__).parent.resolve().__str__()
mrmp_headless_path = os.path.join(working_directory, "mrmp", "mrmp_headless.py")

SCENES_PATHS = [
    "2_gate_easy.json",
    "2_maze.json",
]
ARGUMENTS = [3, 4, 5, 6, 7, 8, 9]

COLUMNS = ["scene_name", "rrt_star"] + [f"my with arg{argument}" for argument in ARGUMENTS]

BASE_COMMAND_TO_RUN = "python {mrmp_headless} --scene={scene} --solver={solver}"

rows = []
for scene_name in SCENES_PATHS:
    row = [f"{scene_name}"]
    print('\x1b[6;30;42m' + scene_name + '\x1b[0m')
    scene_path = os.path.join(working_directory, "mrmp", "scenes", scene_name)
    rrt_command_to_run = BASE_COMMAND_TO_RUN.format(mrmp_headless=mrmp_headless_path,
                                                    scene=scene_path,
                                                    solver=os.path.join(working_directory, "mrmp", "solvers",
                                                                        "rrt_star", "solver.py"))

    print(f"Running the command:\n {rrt_command_to_run}")
    a = os.popen(rrt_command_to_run).read()
    rrt_quality = float(a.split("\n")[-4])
    row.append(f"{rrt_quality}")
    print('\x1b[6;30;42m' + f'RRT_STAR: {rrt_quality}' + '\x1b[0m')
    for argument in ARGUMENTS:
        command_to_run = BASE_COMMAND_TO_RUN.format(mrmp_headless=mrmp_headless_path,
                                                    scene=scene_path,
                                                    solver=os.path.join(working_directory, "mrmp", "solvers",
                                                                        "my_algo", "prm_2_minlen.py"))
        command_to_run += f" --argument=300,{argument}"

        print(f"Running the command:\n {command_to_run}")
        c = os.popen(command_to_run).read()
        my_quality = c.split("\n")[-5]
        row.append(f"{my_quality}")
        print('\x1b[6;30;42m' + f'MY with argument {argument}: {my_quality}' + '\x1b[0m')

    rows.append(row)

df = pd.DataFrame(rows, columns=COLUMNS)
# This df contains for each scene all the results
