import pandas as pd
import numpy as np


def generate_data(num_entries, algorithm_types):
    # Create empty lists to store the data
    image_ids = [f"image{i}" for i in range(num_entries)]
    x1s = np.random.randint(0, 100, size=num_entries).tolist()
    y1s = np.random.randint(0, 100, size=num_entries).tolist()
    x2s = (np.array(x1s) + np.random.randint(10, 50, size=num_entries)).tolist()
    y2s = (np.array(y1s) + np.random.randint(10, 50, size=num_entries)).tolist()
    defect_types = np.random.choice(
        ["defect1", "defect2", "defect3"], size=num_entries
    ).tolist()
    inference_times = np.round(
        np.random.uniform(0.01, 0.1, size=num_entries), 2
    ).tolist()
    algorithm_types_list = np.random.choice(algorithm_types, size=num_entries).tolist()

    return (
        image_ids,
        x1s,
        y1s,
        x2s,
        y2s,
        defect_types,
        inference_times,
        algorithm_types_list,
    )


def generate_mock_data(
    num_entries=10,
    algorithm_types=("algo1", "algo2", "algo3", "algo4"),
    save_to_csv=False,
):
    image_ids, x1s, y1s, x2s, y2s, defect_types, _, _ = generate_data(
        num_entries, algorithm_types
    )
    # Create DataFrames for ground truth and inference data
    gt_data = {
        "image_id": image_ids,
        "x1": x1s,
        "y1": y1s,
        "x2": x2s,
        "y2": y2s,
        "defect_type": defect_types,
    }

    (
        image_ids,
        x1s,
        y1s,
        x2s,
        y2s,
        defect_types,
        inference_times,
        algorithm_types_list,
    ) = generate_data(num_entries, algorithm_types)
    inference_data = {
        "image_id": image_ids,
        "x1": x1s,
        "y1": y1s,
        "x2": x2s,
        "y2": y2s,
        "defect_type": defect_types,
        "inference_time": inference_times,
        "algorithm_type": algorithm_types_list,
    }
    gt_df = pd.DataFrame(gt_data)
    inference_df = pd.DataFrame(inference_data)

    # Optionally save the DataFrames to CSV files
    if save_to_csv:
        gt_df.to_csv("ground_truth.csv", index=False)
        inference_df.to_csv("inference_results.csv", index=False)

    return gt_df, inference_df


# Example usage:
gt_df, inference_df = generate_mock_data(save_to_csv=True)
print(gt_df.head())
print(inference_df.head())
