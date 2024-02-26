import argparse
import json
import csv
import os
from typing import Dict, List, Tuple

run_time = 1


def parse_gt_json(json_file_path: str) -> Tuple[str, List[Dict]]:
    """
    Parses the ground truth JSON file and extracts the object data, along with the image file name.

    Args:
    json_file_path (str): The file path of the JSON file.

    Returns:
    Tuple[str, List[Dict]]: A tuple where the first element is the image file name associated with this JSON,
                            and the second element is a list of ground truth data (each item is a dictionary representing an object).
    """
    with open(json_file_path, "r") as file:
        data = json.load(file)

    objects = data.get("step_1", {}).get("result", [])
    image_file_name = os.path.basename(json_file_path).rsplit(".", 1)[0]

    return image_file_name, objects


def parse_gt_folder(folder_path: str) -> Dict[str, List[Dict]]:
    gt_data = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                image_file_name, objects = parse_gt_json(file_path)
                gt_data[image_file_name] = objects

    return gt_data


def parse_user_json(json_file_path: str) -> List[Tuple[List[Dict], str]]:
    """
    Parses the user JSON file and extracts the object data, along with the image file name.

    Args:
    json_file_path (str): The file path of the JSON file.

    Returns:
    List[Tuple[List[Dict], str]]: A list of tuples, each containing object data and the associated image file name.
    """
    with open(json_file_path, "r") as file:
        data = json.load(file)

    parsed_data = []

    if type(data).__name__ == "dict":
        image_name = data["image_name"]
        objects = data["objects"]
        parsed_data.append((objects, image_name))
    else:
        for item in data:
            image_name = item["image_name"]
            objects = item["objects"]
            parsed_data.append((objects, image_name))

    return parsed_data


def parse_user_folder(folder_path: str) -> List[Tuple[List[Dict], str]]:
    """
    Parses a folder containing multiple user JSON files.

    Args:
    folder_path (str): The file path of the folder containing JSON files.

    Returns:
    List[Tuple[List[Dict], str]]: A list of tuples, each containing object data and the associated image file name.
    """
    user_data = []
    for file in os.listdir(folder_path):
        if file.endswith(".json"):
            file_path = os.path.join(folder_path, file)
            user_data.extend(parse_user_json(file_path))

    return user_data


def process_user_input(input_path: str) -> List[Tuple[List[Dict], str]]:
    """
    Processes the user's input, which can be either a single JSON file or a folder containing multiple JSON files.

    Args:
    input_path (str): The path to the JSON file or folder containing JSON files.

    Returns:
    List[Tuple[List[Dict], str]]: A list of tuples, each containing object data and the associated image file name.
    """
    if os.path.isfile(input_path) and input_path.endswith(".json"):
        return parse_user_json(input_path)
    elif os.path.isdir(input_path):
        return parse_user_folder(input_path)
    else:
        raise ValueError("The input path is neither a JSON file nor a directory.")


def calculate_iou(box1: Dict, box2: Dict) -> float:
    if "x" in box1:
        x1, y1, w1, h1 = box1["x"], box1["y"], box1["width"], box1["height"]
    else:
        print("box1 error")
        exit()
    if "x" in box2:
        x2, y2, w2, h2 = box2["x"], box2["y"], box2["width"], box2["height"]
    else:
        print("box2 error")
        exit()

    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    inter_area = max(xi2 - xi1, 0) * max(yi2 - yi1, 0)

    union_area = w1 * h1 + w2 * h2 - inter_area

    iou = inter_area / union_area if union_area != 0 else 0

    return iou


def match_predictions(gt_data, pred_data, iou_threshold=0.1):
    matched_gt = {}
    matched_preds = {}
    unmatched_preds = {}

    for pred_boxes, img_name in pred_data:
        gt_boxes = gt_data.get(img_name, []).copy()
        matched_gt[img_name] = []
        matched_preds[img_name] = []
        unmatched_preds[img_name] = []

        for pred_box in pred_boxes:
            best_iou = 0
            best_gt_box = None
            for gt_box in gt_boxes:
                iou = calculate_iou(pred_box, gt_box)
                if (
                    iou > best_iou
                    and iou >= iou_threshold
                    and pred_box["attribute"] == gt_box["attribute"]
                ):
                    best_iou = iou
                    best_gt_box = gt_box

            if best_gt_box:
                matched_gt[img_name].append(best_gt_box)
                matched_preds[img_name].append(pred_box)
                gt_boxes.remove(best_gt_box)
            else:
                unmatched_preds[img_name].append(pred_box)

    return matched_gt, matched_preds, unmatched_preds


def group_by_defect_type(matched_gt, matched_preds, unmatched_preds):
    grouped_matched_gt = {}
    grouped_matched_preds = {}
    grouped_unmatched_preds = {}

    for _, boxes in matched_gt.items():
        for box in boxes:
            defect_type = box["attribute"]
            if defect_type not in grouped_matched_gt:
                grouped_matched_gt[defect_type] = []
            grouped_matched_gt[defect_type].append(box)

    for _, boxes in matched_preds.items():
        for box in boxes:
            defect_type = box["attribute"]
            if defect_type not in grouped_matched_preds:
                grouped_matched_preds[defect_type] = []
            grouped_matched_preds[defect_type].append(box)

    for _, boxes in unmatched_preds.items():
        for box in boxes:
            defect_type = box["attribute"]
            if defect_type not in grouped_unmatched_preds:
                grouped_unmatched_preds[defect_type] = []
            grouped_unmatched_preds[defect_type].append(box)

    return grouped_matched_gt, grouped_matched_preds, grouped_unmatched_preds


def calculate_single_item_scores(
    matched_gt, matched_preds, unmatched_preds, total_time, gt_data
):
    scores = {}
    details = {}
    total_images = len(set([img_name for img_name in gt_data]))

    for defect_type in matched_gt:
        gt_boxes_total = [
            box
            for _, boxes in gt_data.items()
            for box in boxes
            if box["attribute"] == defect_type
        ]
        M = len(gt_boxes_total)

        pred_correct_boxes = matched_preds[defect_type]
        pred_incorrect_boxes = unmatched_preds[defect_type]

        M1 = len(pred_correct_boxes)
        M2 = len(pred_incorrect_boxes)

        discovery_rate = M1 / M if M > 0 else 0
        discovery_score = discovery_rate * 60

        false_detection_rate = M2 / M if M > 0 else 0
        false_detection_score = calculate_false_detection_score(false_detection_rate)

        avg_processing_time = (total_time / total_images) if total_images > 0 else 0
        efficiency_score = calculate_efficiency_score(avg_processing_time)

        single_item_score = discovery_score + false_detection_score + efficiency_score
        scores[defect_type] = single_item_score
        details[defect_type] = {
            "discovery_rate": discovery_rate,
            "discovery_score": discovery_score,
            "false_detection_rate": false_detection_rate,
            "false_detection_score": false_detection_score,
            "efficiency_score": efficiency_score,
        }

    return scores, details


false_detection_thresholds = [1, 2, 3, 5, 10, float("inf")]
false_detection_scores = [30, 25, 20, 10, 5, 0]

efficiency_thresholds = [2, 3, 4, 5, 6, float("inf")]
efficiency_scores = [10, 8, 5, 3, 1, 0]


def calculate_score(value, thresholds, scores):
    for i, threshold in enumerate(thresholds):
        if value <= threshold:
            return scores[i]

    return scores[-1]


def calculate_false_detection_score(W):
    return calculate_score(W, false_detection_thresholds, false_detection_scores)


def calculate_efficiency_score(T):
    return calculate_score(T, efficiency_thresholds, efficiency_scores)


def calculate_total_score(single_item_scores, gt_label_set, defect_weights=None):
    if not defect_weights:
        defect_weights = {defect_type: 1 for defect_type in gt_label_set}

    total_score = 0
    total_weight = sum(defect_weights.values())

    for defect_type, score in single_item_scores.items():
        weight = defect_weights.get(defect_type, 1)
        total_score += score * weight

    return total_score / total_weight if total_weight > 0 else 0


def calculate_overall_metrics(
    matched_gt, matched_preds, unmatched_preds, gt_data, total_time
):
    total_images = len(gt_data)

    total_gt_boxes = sum(len(boxes) for boxes in gt_data.values())
    total_correct_matches = sum(len(matches) for matches in matched_preds.values())
    total_false_detections = sum(
        len(detections) for detections in unmatched_preds.values()
    )

    overall_discovery_rate = (
        total_correct_matches / total_gt_boxes if total_gt_boxes > 0 else 0
    )
    overall_false_detection_rate = (
        total_false_detections / total_gt_boxes if total_gt_boxes > 0 else 0
    )

    overall_discovery_score = overall_discovery_rate * 60
    overall_false_detection_score = calculate_false_detection_score(
        overall_false_detection_rate
    )

    avg_processing_time = total_time / total_images if total_images > 0 else 0
    overall_efficiency_score = calculate_efficiency_score(avg_processing_time)

    return {
        "overall_discovery_rate": overall_discovery_rate,
        "overall_discovery_score": overall_discovery_score,
        "overall_false_detection_rate": overall_false_detection_rate,
        "overall_false_detection_score": overall_false_detection_score,
        "overall_efficiency_score": overall_efficiency_score,
    }


def print_formatted_scores(score_details, total_score, gt_label_set, overall_metrics):
    print(
        f"{'Defect Type':<20} {'Discovery Rate':<20} {'Discovery Score':<20} {'False Detection Rate':<25} {'False Detection Score':<25} {'Efficiency Score':<20}"
    )
    print("-" * 130)

    for defect_type, details in score_details.items():
        print(
            f"{defect_type:<20} {details['discovery_rate'] * 100:<20.2f} {details['discovery_score']:<20.2f} {details['false_detection_rate']:<25.2f} {details['false_detection_score']:<25} {details['efficiency_score']:<20}"
        )

    for label in gt_label_set:
        if label in score_details:
            continue
        else:
            print(f"{label:<20} {0:<20.2f} {0:<20.2f} {0:<25.2f} {0:<25} {0:<20}")

    print(
        f"{'Total':<20} {overall_metrics['overall_discovery_rate'] * 100:<20.2f} {overall_metrics['overall_discovery_score']:<20.2f} {overall_metrics['overall_false_detection_rate']:<25.2f} {overall_metrics['overall_false_detection_score']:<25} {overall_metrics['overall_efficiency_score']:<20}"
    )

    print("\nTotal Score:", total_score)


def save_scores_to_csv(
    score_details, total_score, gt_label_set, filename, overall_metrics
):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "Defect Type",
                "Discovery Rate",
                "Discovery Score",
                "False Detection Rate",
                "False Detection Score",
                "Efficiency Score",
            ]
        )

        for defect_type, details in score_details.items():
            writer.writerow(
                [
                    defect_type,
                    f"{details['discovery_rate'] * 100:.2f}",
                    f"{details['discovery_score']:.2f}",
                    f"{details['false_detection_rate']:.2f}",
                    f"{details['false_detection_score']:.2f}",
                    f"{details['efficiency_score']}",
                ]
            )

        for label in gt_label_set:
            if label in score_details:
                continue
            else:
                writer.writerow(
                    [
                        label,
                        f"{0:.2f}",
                        f"{0:.2f}",
                        f"{0:.2f}",
                        f"{0:.2f}",
                        f"{0}",
                    ]
                )

        writer.writerow(
            [
                "Total",
                f"{overall_metrics['overall_discovery_rate'] * 100:.2f}",
                f"{overall_metrics['overall_discovery_score']:.2f}",
                f"{overall_metrics['overall_false_detection_rate']:.2f}",
                f"{overall_metrics['overall_false_detection_score']:.2f}",
                f"{overall_metrics['overall_efficiency_score']}",
            ]
        )
        writer.writerow(["Total Score", "", "", "", "", total_score])


def get_gt_data_label(gt_data):
    gt_label_set = set()

    for _, value in gt_data.items():
        for item in value:
            gt_label_set.add(item["attribute"])
    return gt_label_set


def main(gt_folder_path, user_folder_path, csv_path):
    gt_data = parse_gt_folder(gt_folder_path)

    gt_label_set = get_gt_data_label(gt_data)

    predict_data = process_user_input(user_folder_path)

    matched_gt, matched_preds, unmatched_preds = match_predictions(
        gt_data, predict_data
    )

    (
        grouped_matched_gt,
        grouped_matched_preds,
        grouped_unmatched_preds,
    ) = group_by_defect_type(matched_gt, matched_preds, unmatched_preds)

    single_item_scores, score_details = calculate_single_item_scores(
        grouped_matched_gt,
        grouped_matched_preds,
        grouped_unmatched_preds,
        run_time,
        gt_data,
    )

    total_score = calculate_total_score(single_item_scores, gt_label_set)

    overall_metrics = calculate_overall_metrics(
        matched_gt, matched_preds, unmatched_preds, gt_data, run_time
    )

    print_formatted_scores(score_details, total_score, gt_label_set, overall_metrics)

    save_scores_to_csv(
        score_details, total_score, gt_label_set, csv_path, overall_metrics
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ground truth and user data.")
    parser.add_argument(
        "gt_folder_path", type=str, help="Path to the ground truth folder"
    )
    parser.add_argument(
        "user_folder_path", type=str, help="Path to the user result folder"
    )
    parser.add_argument("csv_path", type=str, help="Path to save the output CSV file")

    args = parser.parse_args()

    main(args.gt_folder_path, args.user_folder_path, args.csv_path)
