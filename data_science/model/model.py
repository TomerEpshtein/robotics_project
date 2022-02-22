# Spliting arrays or matrices into random train and test subsets
import csv
import os
import pathlib
import operator

import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split


def get_best_result(row):
    min_value = min(row)
    min_index = row.index(min_value)
    return min_index + 3


working_directory = pathlib.Path(__file__).parent.parent.parent.resolve().__str__()
best_results = []
all_results = []
with open(os.path.join(working_directory, "results.csv")) as csvfile:
    rows = csv.reader(csvfile)
    for row in rows:
        if row[0] == "scene_name":
            continue
        best_result = get_best_result(row[2:])
        all_results.append(row[2:])
        best_results.append(best_result)


all_features_rows = []
with open(os.path.join(working_directory, 'data_science', "features", "all_features.csv"), "r") as csvfile:
    rows = csv.reader(csvfile)
    for row in rows:
        if row[0] == "scene_name":
            continue
        all_features_rows.append(row)


def get_row_index(some_row):
    row_as_list = some_row.tolist()
    row_as_list = [str(a) for a in row_as_list]
    for i in range(len(all_features_rows)):
        for j in range(6):
            if round(float(row_as_list[j]), 2) != round(float(all_features_rows[i][1:][j]), 2):
                break
            return i
    raise Exception("Shouldn't get here")


TEST_SIZE = 0.2
NUM_ROUNDS = 100


def read_data_and_split():
    working_directory = pathlib.Path(__file__).parent.parent.parent.resolve().__str__()
    df = pd.read_csv(os.path.join(working_directory, "data_science", "model", "data.csv"))
    df = df.drop(["scene_name"], axis=1)
    X, y = df.drop(["chunk_size"], axis=1), df["chunk_size"]
    X_train, X_test, y_train, y_test = train_test_split(X.values, y.values, test_size=TEST_SIZE)
    return X_train, X_test, y_train, y_test


def linear_regression_model(X_train, y_train):
    reg = LinearRegression()
    reg.fit(X_train, y_train)
    return reg


def random_forest_model(X_train, y_train):
    rfr = RandomForestClassifier()
    rfr.fit(X_train, y_train)
    return rfr


def xgb_model(X_train, y_train):
    # xgb_reg = xgb.XGBRegressor(objective='reg:squarederror', colsample_bytree=0.3, learning_rate=0.1,
    #                            max_depth=5, alpha=10, n_estimators=10)
    xgb_reg = xgb.XGBRegressor()
    xgb_reg.fit(X_train, y_train)
    return xgb_reg


def get_diff(first, second):
    return (second-first) / first


def check_base_model():
    reg_score = 0
    reg_diff = 0
    rfr_score = 0
    rfr_diff = 0
    xgb_score = 0
    xgb_diff = 0
    for _ in range(NUM_ROUNDS):
        X_train, X_test, y_train, y_test = read_data_and_split()

        reg = linear_regression_model(X_train, y_train)
        rfr = random_forest_model(X_train, y_train)
        xgb_m = xgb_model(X_train, y_train)

        for i in range(len(X_test)):
            row_index_of_current_sample = get_row_index(X_test[i])
            best_result_of_current_sample = float(all_results[row_index_of_current_sample][y_test[i]-3])

            reg_result_of_current_sample = all_results[row_index_of_current_sample][round(reg.predict([X_test[i]])[0])-3]
            if round(reg.predict([X_test[i]])[0]) == y_test[i]\
                    or best_result_of_current_sample == reg_result_of_current_sample:
                reg_score += 1

            reg_diff += get_diff(best_result_of_current_sample, float(reg_result_of_current_sample))

            rfr_result_of_current_sample = all_results[row_index_of_current_sample][rfr.predict([X_test[i]])[0]-3]
            if rfr.predict([X_test[i]]) == y_test[i]\
                    or best_result_of_current_sample == rfr_result_of_current_sample:
                rfr_score += 1
            rfr_diff += get_diff(best_result_of_current_sample, float(rfr_result_of_current_sample))

            xgb_index = round(xgb_m.predict([X_test[i]])[0])-3 if round(xgb_m.predict([X_test[i]])[0])-3 <= 6 else 6
            xgb_m_result_of_current_sample = all_results[row_index_of_current_sample][xgb_index]
            if round(xgb_m.predict([X_test[i]])[0]) == y_test[i]\
                    or best_result_of_current_sample == xgb_m_result_of_current_sample:
                xgb_score += 1
            xgb_diff += get_diff(best_result_of_current_sample, float(xgb_m_result_of_current_sample))

    # average accuracy percent
    print(rfr_score/NUM_ROUNDS / (TEST_SIZE*100))
    print(rfr_diff/NUM_ROUNDS / (TEST_SIZE*100))
    print(reg_score/NUM_ROUNDS / (TEST_SIZE*100))
    print(reg_diff/NUM_ROUNDS / (TEST_SIZE*100))
    print(xgb_score/NUM_ROUNDS / (TEST_SIZE*100))
    print(xgb_diff/NUM_ROUNDS / (TEST_SIZE*100))


# check_base_model()


def xgb_many_models():
    all_models = {}
    for n_estimator in [10, 50, 100]:
        for max_depth in [5, 10, 50]:
            for learning_rate in [0.1, 0.2, 0.3]:
                for colsample_bytree in [0.2, 0.4, 0.6]:
                    xgb_reg = xgb.XGBRegressor(n_estimator=n_estimator,
                                               max_depth=max_depth,
                                               learning_rate=learning_rate,
                                               colsample_bytree=colsample_bytree)

                    all_models[f"{n_estimator},{max_depth},{learning_rate},{colsample_bytree}"] = xgb_reg
    return all_models


def check_best_xgb():
    all_scores = {}
    all_diffs = {}
    for _ in range(NUM_ROUNDS):
        all_models = xgb_many_models()
        X_train, X_test, y_train, y_test = read_data_and_split()

        for model_key in all_models.keys():
            current_model = all_models[model_key]
            current_model.fit(X_train, y_train)
            for i in range(len(X_test)):
                row_index_of_current_sample = get_row_index(X_test[i])
                best_result_of_current_sample = float(all_results[row_index_of_current_sample][y_test[i] - 3])
                xgb_index = round(current_model.predict([X_test[i]])[0]) - 3 if round(current_model.predict([X_test[i]])[0]) - 3 <= 6 else 6
                xgb_m_result_of_current_sample = all_results[row_index_of_current_sample][xgb_index]
                if float(xgb_m_result_of_current_sample) == best_result_of_current_sample:
                    if model_key not in all_scores:
                        all_scores[model_key] = 1/(100*TEST_SIZE*NUM_ROUNDS)
                    else:
                        all_scores[model_key] += 1/(100*TEST_SIZE*NUM_ROUNDS)
                if model_key not in all_diffs:
                    all_diffs[model_key] = get_diff(best_result_of_current_sample,
                                                    float(xgb_m_result_of_current_sample))/(100*TEST_SIZE*NUM_ROUNDS)
                else:
                    all_diffs[model_key] += get_diff(best_result_of_current_sample,
                                                     float(xgb_m_result_of_current_sample))/(100*TEST_SIZE*NUM_ROUNDS)

    best_model_key = max(all_scores.items(), key=operator.itemgetter(1))[0]
    print(best_model_key)
    print(all_scores[best_model_key])
    print(all_diffs[best_model_key])


# check_best_xgb()


def check_baseline():
    baseline_score = 0
    baseline_diff = 0
    for _ in range(NUM_ROUNDS):
        X_train, X_test, y_train, y_test = read_data_and_split()

        for i in range(len(X_test)):
            row_index_of_current_sample = get_row_index(X_test[i])
            best_result_of_current_sample = float(all_results[row_index_of_current_sample][y_test[i] - 3])
            baseline_result_of_current_sample = all_results[row_index_of_current_sample][1]
            if float(baseline_result_of_current_sample) == best_result_of_current_sample:
                baseline_score += 1 / (100 * TEST_SIZE * NUM_ROUNDS)

            baseline_diff += get_diff(best_result_of_current_sample,
                                      float(baseline_result_of_current_sample)) / (100 * TEST_SIZE * NUM_ROUNDS)

    print(baseline_score)
    print(baseline_diff)


check_baseline()
