import csv
import os
import pathlib
import time

working_directory = pathlib.Path(__file__).parent.resolve().__str__()
mrmp_headless_path = os.path.join(working_directory, "mrmp", "mrmp_headless.py")

SCENES_PATHS = [f"{i}.json" for i in range(1, 101)]
ARGUMENTS = [3, 4, 5, 6, 7, 8, 9]
COLUMNS = ["scene_name", "rrt_star"] + [f"arg={argument}" for argument in ARGUMENTS]

BASE_COMMAND_TO_RUN = "python {mrmp_headless} --scene={scene} --solver={solver}"

rows = []
time_rows = []
for scene_name in SCENES_PATHS:
    row = {"scene_name": f"{scene_name}"}
    time_row = {"scene_name": f"{scene_name}"}
    print('\x1b[6;31;32m' + scene_name + '\x1b[0m')
    scene_path = os.path.join(working_directory, "mrmp", "scenes", scene_name)
    rrt_command_to_run = BASE_COMMAND_TO_RUN.format(mrmp_headless=mrmp_headless_path,
                                                    scene=scene_path,
                                                    solver=os.path.join(working_directory, "mrmp", "solvers",
                                                                        "rrt_star", "solver.py"))

    print(f"Running the command:\n {rrt_command_to_run}")
    rrt_quality = 0
    time_to_run = 0
    for _ in range(10):
        a0 = time.time()
        a = os.popen(rrt_command_to_run).read()
        a1 = time.time()
        rrt_quality += float(a.split("\n")[-4])
        time_to_run += (a1-a0)

    row["rrt_star"] = f"{rrt_quality/10}"
    time_row["rrt_star"] = f"{time_to_run/10}"
    print('\x1b[6;30;42m' + f'RRT_STAR: {rrt_quality/10}' + '\x1b[0m')

    for argument in ARGUMENTS:
        num_landmarks = 300
        command_to_run = BASE_COMMAND_TO_RUN.format(mrmp_headless=mrmp_headless_path,
                                                    scene=scene_path,
                                                    solver=os.path.join(working_directory, "mrmp", "solvers",
                                                                        "my_algo", "prm_2_minlen.py"))
        command_to_run += f" --argument={num_landmarks},{argument}"

        print(f"Running the command:\n {command_to_run}")
        my_quality = 0
        time_to_run = 0
        for _ in range(10):
            inner_stop = False
            while not inner_stop:
                a0 = time.time()
                c = os.popen(command_to_run).read()
                a1 = time.time()
                inner_quality = c.split("\n")[-5]
                try:
                    float(inner_quality)
                    time_to_run += (a1-a0)
                    inner_stop = True
                    my_quality += float(inner_quality)
                except ValueError:
                    # in case we didn't succeed try again with higher
                    num_landmarks = 2 * num_landmarks
                    continue

        row[f"arg={argument}"] = f"{my_quality/10}"
        time_row[f"arg={argument}"] = f"{time_to_run / 10}"
        print('\x1b[6;30;42m' + f'MY with argument {argument}: {my_quality/10}' + '\x1b[0m')

    rows.append(row)
    time_rows.append(time_row)


with open('results.csv', 'w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)

    writer.writeheader()
    for row in rows:
        writer.writerow(row)

with open('times.csv', 'w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)

    writer.writeheader()
    for row in time_rows:
        writer.writerow(row)
