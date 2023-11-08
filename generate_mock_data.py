import pandas as pd
import numpy as np


def generate_ground_truth(num_images=10, max_defects_per_image=3):
    ground_truth_data = []
    for i in range(num_images):
        num_defects = np.random.randint(1, max_defects_per_image + 1)
        for _ in range(num_defects):
            ground_truth_data.append(
                {
                    "image_id": f"image{i}",
                    "x1": np.random.randint(0, 100),
                    "y1": np.random.randint(0, 100),
                    "x2": np.random.randint(100, 150),
                    "y2": np.random.randint(100, 150),
                    "defect_type": np.random.choice(["defect1", "defect2", "defect3"]),
                }
            )
    return pd.DataFrame(ground_truth_data)


def generate_inference(
    num_images=10,
    avg_defects_per_image=4,
    algorithm_types=("algo1", "algo2", "algo3", "algo4"),
):
    inference_data = []
    # Determine total inference time for each algorithm type
    total_inference_time = {algo: np.random.uniform(1, 10) for algo in algorithm_types}

    for i in range(num_images):
        num_defects = np.random.poisson(avg_defects_per_image)
        for _ in range(num_defects):
            algo_type = np.random.choice(algorithm_types)
            inference_data.append(
                {
                    "image_id": f"image{i}",
                    "x1": np.random.randint(0, 100),
                    "y1": np.random.randint(0, 100),
                    "x2": np.random.randint(100, 150),
                    "y2": np.random.randint(100, 150),
                    "defect_type": np.random.choice(["defect1", "defect2", "defect3"]),
                    "algorithm_type": algo_type,
                    "total_inference_time": total_inference_time[
                        algo_type
                    ],  # Use the fixed total time for this algorithm
                }
            )
    return pd.DataFrame(inference_data)


# Generate ground truth and inference data
gt_df = generate_ground_truth()
inference_df = generate_inference()

# Save the data to CSV files
gt_df.to_csv("ground_truth.csv", index=False)
inference_df.to_csv("inference_results.csv", index=False)

print("Ground Truth saved to 'ground_truth.csv'")
print("Inference Results saved to 'inference_results.csv'")
