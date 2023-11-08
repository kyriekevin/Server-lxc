import pandas as pd
import argparse


# Function to calculate the Intersection over Union (IoU) of two bounding boxes
def calculate_iou(boxA, boxB):
    # Ensure that the coordinates are non-negative numbers
    if not all(isinstance(coord, (int, float)) and coord >= 0 for coord in boxA + boxB):
        raise ValueError("Coordinates must be non-negative numbers.")

    # Ensure that the coordinates are in the correct order (x1 < x2 and y1 < y2)
    if not (boxA[0] < boxA[2] and boxA[1] < boxA[3]):
        raise ValueError("BoxA coordinates are not in the correct order.")
    if not (boxB[0] < boxB[2] and boxB[1] < boxB[3]):
        raise ValueError("BoxB coordinates are not in the correct order.")

    # Calculate the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Compute the area of intersection rectangle
    interArea = max(0, xB - xA) * max(0, yB - yA)

    # Compute the area of both the prediction and ground-truth rectangles
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # Compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)

    return iou


# Define the thresholds and corresponding scores for false detection and efficiency
false_detection_thresholds = [1, 2, 3, 5, 10, float("inf")]
false_detection_scores = [30, 25, 20, 10, 5, 0]

efficiency_thresholds = [2, 3, 4, 5, 6, float("inf")]
efficiency_scores = [10, 8, 5, 3, 1, 0]


def calculate_score(value, thresholds, scores):
    # Add a check for the case when value is exactly on a threshold
    for i, threshold in enumerate(thresholds):
        if value <= threshold:
            return scores[i]

    # If value is greater than all thresholds, return the last score
    return scores[-1]


def calculate_false_detection_score(W):
    return calculate_score(W, false_detection_thresholds, false_detection_scores)


def calculate_efficiency_score(T):
    return calculate_score(T, efficiency_thresholds, efficiency_scores)


# Adjust the configure_evaluation function to return a dictionary of weights
def configure_evaluation(iou_threshold, weights, inference_df):
    # Convert the weights string into a dictionary if provided
    weights_dict = {}
    if weights:
        for item in weights.split(","):
            algo, weight = item.split(":")
            algo = algo.strip()
            if algo in inference_df["algorithm_type"].unique():
                weights_dict[algo] = float(weight.strip())
            else:
                raise ValueError(
                    f"Algorithm type '{algo}' specified in weights is not present in the inference data."
                )
    else:
        # If weights are not provided, set default weight of 1 for each algorithm type found in inference_df
        algorithm_types = inference_df["algorithm_type"].unique()
        weights_dict = {algo_type: 1 for algo_type in algorithm_types}

    return iou_threshold, weights_dict


# Function to calculate the individual score for a defect type
def calculate_individual_score(M1, M, M2, total_time, num_images):
    detection_rate_score = (M1 / M) * 60 if M else 0
    false_detection_score = calculate_false_detection_score(M2 / M) if M else 0
    efficiency_score = (
        calculate_efficiency_score(total_time / num_images) if num_images else 0
    )
    return (
        detection_rate_score + false_detection_score + efficiency_score,
        detection_rate_score,
        false_detection_score,
        efficiency_score,
    )


# Function to calculate the overall score for all defect types
def calculate_overall_score(individual_scores, weights):
    if sum(weights) == 0:
        return 0
    return sum(
        score * weight for score, weight in zip(individual_scores, weights)
    ) / sum(weights)


# Main evaluation function encapsulating the whole process
def evaluate_algorithm(gt_df, inference_df, iou_threshold, weights):
    # Create a dictionary to hold scores for each algorithm type
    scores_by_type = {}

    # Get a list of unique algorithm types from the inference data
    algorithm_types = inference_df["algorithm_type"].unique()

    # Get the total inference time for each algorithm from the first instance, assuming it's the same for all instances of the algorithm.
    total_time_by_algorithm = (
        inference_df.groupby("algorithm_type")["total_inference_time"].first().to_dict()
    )

    # Iterate over each algorithm type to calculate individual scores
    for algorithm_type in algorithm_types:
        # Filter the inference results for the current algorithm type
        inference_df_type = inference_df[
            inference_df["algorithm_type"] == algorithm_type
        ].copy()  # Make a copy to avoid warning

        # Initialize the 'correct' column as boolean type before any assignment
        inference_df_type["correct"] = False
        inference_df_type["correct"] = inference_df_type["correct"].astype("bool")

        # Calculate the total number of images evaluated by the algorithm
        num_images_evaluated_by_algorithm = inference_df_type["image_id"].nunique()

        # Calculate IOU and determine correct detections for the current type
        for i, inf_row in inference_df_type.iterrows():
            gt_boxes = gt_df[
                (gt_df["image_id"] == inf_row["image_id"])
                & (gt_df["defect_type"] == inf_row["defect_type"])
            ]
            correct_detection = False
            for _, gt_row in gt_boxes.iterrows():
                iou_score = calculate_iou(
                    inf_row[["x1", "y1", "x2", "y2"]].tolist(),
                    gt_row[["x1", "y1", "x2", "y2"]].tolist(),
                )
                if iou_score >= iou_threshold:
                    correct_detection = True
                    break
            # Use .loc to set the value and explicitly cast to boolean
            inference_df_type.loc[i, "correct"] = bool(correct_detection)

        # Calculate scores for the current algorithm type
        M = len(gt_df)
        M1 = inference_df_type["correct"].sum()
        M2 = len(inference_df_type) - M1

        # Calculate the efficiency score based on the average time taken per image
        total_time = total_time_by_algorithm[algorithm_type]
        average_time_per_image = (
            total_time / num_images_evaluated_by_algorithm
            if num_images_evaluated_by_algorithm
            else float("inf")
        )
        efficiency_score = calculate_efficiency_score(average_time_per_image)

        detection_rate_score = (M1 / M) * 60 if M else 0
        false_detection_score = calculate_false_detection_score(M2 / M) if M else 0

        individual_score = (
            detection_rate_score + false_detection_score + efficiency_score
        )

        # Add the scores to the dictionary with algorithm type as key
        scores_by_type[algorithm_type] = {
            "Detection Rate Score": detection_rate_score,
            "False Detection Score": false_detection_score,
            "Efficiency Score": efficiency_score,
            "Individual Score": individual_score,
        }

    # Calculate the overall score by weighting the individual scores
    overall_score = 0
    total_weight = sum(weights.values())
    for algorithm_type, scores in scores_by_type.items():
        weight = weights.get(
            algorithm_type, 1
        )  # Get the weight for the algorithm type, defaulting to 1
        overall_score += scores["Individual Score"] * weight
    if total_weight > 0:
        overall_score /= total_weight

    return scores_by_type, overall_score


# Main function to run the evaluation
def main(gt_csv, inference_csv, iou_threshold, weights):
    # Read the ground truth and inference data from CSV files
    gt_df = pd.read_csv(gt_csv)
    inference_df = pd.read_csv(inference_csv)

    # Configure the evaluation settings
    iou_threshold, weights = configure_evaluation(iou_threshold, weights, inference_df)

    # Evaluate the algorithm
    scores_by_type, overall_score = evaluate_algorithm(
        gt_df, inference_df, iou_threshold, weights
    )

    # Print the scores in alphabetical order of the algorithm types
    for algo_type in sorted(scores_by_type.keys()):
        scores = scores_by_type[algo_type]
        print(f"Scores for {algo_type}:")
        for score_name, score_value in sorted(scores.items()):
            print(f"{score_name}: {score_value}")
        print()

    print(f"Overall Score: {overall_score}")


# If this script is executed (rather than imported as a module), run the main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate object detection algorithms."
    )
    parser.add_argument(
        "--gt_csv",
        type=str,
        default="./ground_truth.csv",
        help="Path to the ground truth CSV file.",
    )
    parser.add_argument(
        "--inference_csv",
        type=str,
        default="./inference_results.csv",
        help="Path to the inference results CSV file.",
    )
    parser.add_argument(
        "--iou_threshold", type=float, default=0.5, help="IoU threshold for evaluation."
    )
    parser.add_argument(
        "--weights",
        help="Comma-separated list of weights for algorithm types (e.g., 'algo1:1,algo2:2').",
    )

    args = parser.parse_args()

    main(args.gt_csv, args.inference_csv, args.iou_threshold, args.weights)
