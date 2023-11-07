import pandas as pd


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


# Function to configure the evaluation settings
def configure_evaluation(iou_threshold=0.5, weights=None):
    if weights is None:
        weights = [1]  # Default weights (equal for all defect types)
    return iou_threshold, weights


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
    # Calculate IOU and determine correct detections
    inference_df["correct"] = False
    for i, inf_row in inference_df.iterrows():
        gt_boxes = gt_df[
            (gt_df["image_id"] == inf_row["image_id"])
            & (gt_df["defect_type"] == inf_row["defect_type"])
        ]
        for _, gt_row in gt_boxes.iterrows():
            iou_score = calculate_iou(
                inf_row[["x1", "y1", "x2", "y2"]].values,
                gt_row[["x1", "y1", "x2", "y2"]].values,
            )
            if iou_score >= iou_threshold:
                inference_df.at[i, "correct"] = True
                break

    # Calculate scores
    M = len(gt_df)
    M1 = inference_df["correct"].sum()
    M2 = len(inference_df) - M1
    total_time = inference_df["inference_time"].sum()
    num_images = gt_df["image_id"].nunique()
    (
        individual_score,
        detection_rate_score,
        false_detection_score,
        efficiency_score,
    ) = calculate_individual_score(M1, M, M2, total_time, num_images)

    # Calculate overall score
    overall_score = calculate_overall_score([individual_score] * len(weights), weights)

    return {
        "Detection Rate Score": detection_rate_score,
        "False Detection Score": false_detection_score,
        "Efficiency Score": efficiency_score,
        "Individual Score": individual_score,
        "Overall Score": overall_score,
    }


# Main function to run the evaluation
def main():
    # Configure the evaluation settings
    iou_threshold, weights = configure_evaluation()

    # Read the ground truth and inference data from CSV files
    gt_df = pd.read_csv("./gt.csv")
    inference_df = pd.read_csv("./inference.csv")

    # Evaluate the algorithm
    scores = evaluate_algorithm(gt_df, inference_df, iou_threshold, weights)

    # Print the scores
    for score_name, score_value in scores.items():
        print(f"{score_name}: {score_value}")


# If this script is executed (rather than imported as a module), run the main function
if __name__ == "__main__":
    main()
