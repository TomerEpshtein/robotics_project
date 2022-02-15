import csv
import statistics

times_rows = []
with open('times.csv', newline='') as csvfile:
    r = csv.reader(csvfile)
    for row in r:
        if row[0] == "scene_name":
            continue
        times_rows.append(row)

results_rows = []
with open('results.csv', newline='') as csvfile:
    r = csv.reader(csvfile)
    for row in r:
        if row[0] == "scene_name":
            continue
        results_rows.append(row)

counter_for_the_best = [0] + [0 for _ in range(3, 10)]
improvement = []
time_diff = []
j = 0
for i in range(100):
    row = results_rows[i]
    just_results = row[1:]
    just_results = [float(res) for res in just_results]
    rrt_result = just_results[0]
    best_result = min(just_results)
    improvement.append((rrt_result - best_result)/rrt_result)
    best_result_index = just_results.index(best_result)
    counter_for_the_best[best_result_index] += 1

    rrt_star_time = float(times_rows[i][1])
    best_result_time = float(times_rows[i][best_result_index+1])
    if best_result_time < rrt_star_time:
        j += 1
    time_diff.append((rrt_star_time - best_result_time)/rrt_star_time)


print(counter_for_the_best)
print(statistics.mean(improvement))
print(max(improvement))
print(time_diff)
print(j)
