"""
Organize all the features and also the chunk_size in the same csv
"""
import csv
import os


def get_best_result(row):
    min_value = min(row)
    min_index = row.index(min_value)
    return min_index + 3


working_directory = "C:\\Users\\eps\\Desktop\\epshtein\\project\\git"
all_rows = []
with open(os.path.join(working_directory, 'data_science', "features", "all_features.csv"), "r") as csvfile:
    rows = csv.reader(csvfile)
    for row in rows:
        if row[0] == "scene_name":
            continue
        all_rows.append(row)

best_results = []
with open(os.path.join(working_directory, "results.csv")) as csvfile:
    rows = csv.reader(csvfile)
    for row in rows:
        if row[0] == "scene_name":
            continue
        best_result = get_best_result(row[2:])
        best_results.append(best_result)

COLUMNS = ["scene_name","total_area",
           "robots_distance","max_transition_required",
           "is_linear","prm_length","prm_quality","chunk_size"]

with open('data.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(COLUMNS)
    for i in range(100):
        current_row = all_rows[i]
        current_row.append(best_results[i])
        writer.writerow(current_row)

a = 1