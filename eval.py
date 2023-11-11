import json
import os
import random
from typing import Dict, List, Tuple

gt_folder_path = "./8类缺陷/"
user_folder_path = "./inferece.json"
run_time = 100


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
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                image_file_name, objects = parse_gt_json(file_path)
                gt_data[image_file_name] = objects

    return gt_data


def generate_mock_predictions(
    gt_data: Dict[str, List[Tuple[List[Dict], str]]], output_file: str
):
    mock_predictions = []

    for _, objects_info in gt_data.items():
        for objects, image_file_name in objects_info:
            mock_objects = []
            for obj in objects:
                if random.random() < 0.8:
                    mock_obj = {
                        "x": obj["x"] + random.randint(-10, 10),
                        "y": obj["y"] + random.randint(-10, 10),
                        "width": obj["width"] + random.randint(-10, 10),
                        "height": obj["height"] + random.randint(-10, 10),
                        "attribute": obj["attribute"],
                    }
                    mock_objects.append(mock_obj)
                extra_predictions_rate = random.randint(0, 5)
                for _ in range(extra_predictions_rate):
                    mock_obj = {
                        "x": random.randint(0, 1000),
                        "y": random.randint(0, 1000),
                        "width": random.randint(10, 100),
                        "height": random.randint(10, 100),
                        "attribute": obj["attribute"],
                    }
                    mock_objects.append(mock_obj)

            mock_predictions.append(
                {"image_name": image_file_name, "objects": mock_objects}
            )

    # 将模拟预测写入文件
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(mock_predictions, file, indent=4, ensure_ascii=False)


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
        # Single JSON file
        return parse_user_json(input_path)
    elif os.path.isdir(input_path):
        # Folder containing multiple JSON files
        return parse_user_folder(input_path)
    else:
        raise ValueError("The input path is neither a JSON file nor a directory.")


def calculate_iou(box1: Dict, box2: Dict) -> float:
    x1, y1, w1, h1 = box1["x"], box1["y"], box1["width"], box1["height"]
    x2, y2, w2, h2 = box2["x"], box2["y"], box2["width"], box2["height"]

    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    inter_area = max(xi2 - xi1, 0) * max(yi2 - yi1, 0)

    union_area = w1 * h1 + w2 * h2 - inter_area

    iou = inter_area / union_area if union_area != 0 else 0

    return iou


def match_predictions(gt_data, pred_data, iou_threshold=0.5):
    matched_gt = {}
    matched_preds = {}
    unmatched_preds = {}

    for pred_boxes, img_name in pred_data:
        gt_boxes = gt_data.get(img_name, [])
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
                gt_boxes.remove(best_gt_box)  # 避免重复匹配
            else:
                unmatched_preds[img_name].append(pred_box)

    return matched_gt, matched_preds, unmatched_preds


def group_by_defect_type(matched_gt, matched_preds, unmatched_preds):
    grouped_matched_gt = {}
    grouped_matched_preds = {}
    grouped_unmatched_preds = {}

    for img_name, boxes in matched_gt.items():
        for box in boxes:
            defect_type = box["attribute"]
            if defect_type not in grouped_matched_gt:
                grouped_matched_gt[defect_type] = []
            grouped_matched_gt[defect_type].append(box)

    for img_name, boxes in matched_preds.items():
        for box in boxes:
            defect_type = box["attribute"]
            if defect_type not in grouped_matched_preds:
                grouped_matched_preds[defect_type] = []
            grouped_matched_preds[defect_type].append(box)

    for img_name, boxes in unmatched_preds.items():
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
    total_images = len(set([img_name for img_name in gt_data]))  # 计算总图像数量

    # 假设matched_gt, matched_preds, unmatched_preds已经按缺陷类型分组
    for defect_type in matched_gt:
        gt_boxes = matched_gt[defect_type]
        pred_correct_boxes = matched_preds[defect_type]
        pred_incorrect_boxes = unmatched_preds[defect_type]

        M = len(gt_boxes)  # 标准框总数
        M1 = len(pred_correct_boxes)  # 正确匹配的框数
        M2 = len(pred_incorrect_boxes)  # 错误匹配的框数

        # 计算发现率得分
        discovery_rate = M1 / M if M > 0 else 0
        discovery_score = discovery_rate * 60

        # 计算误检比得分
        false_detection_rate = M2 / M if M > 0 else 0
        false_detection_score = calculate_false_detection_score(false_detection_rate)

        # 计算识别效率得分
        # 计算每种缺陷类型对应的图像数量
        defect_type_images = len(
            set(
                [
                    img_name
                    for img_name, boxes in gt_data.items()
                    if any(box["attribute"] == defect_type for box in boxes)
                ]
            )
        )
        # 计算每种类型的平均处理时间
        avg_processing_time = (
            (total_time * defect_type_images / total_images) if total_images > 0 else 0
        )
        efficiency_score = calculate_efficiency_score(avg_processing_time)

        # 计算单项识别效果得分
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


def calculate_total_score(single_item_scores, defect_weights=None):
    if not defect_weights:
        # 如果没有提供权重，则假定所有缺陷类型权重相同
        defect_weights = {defect_type: 1 for defect_type in single_item_scores}

    total_score = 0
    total_weight = sum(defect_weights.values())

    for defect_type, score in single_item_scores.items():
        weight = defect_weights.get(defect_type, 1)
        total_score += score * weight

    return total_score / total_weight if total_weight > 0 else 0


def print_formatted_scores(score_details, total_score):
    # 打印表头
    print(
        f"{'Defect Type':<20} {'Discovery Rate':<20} {'Discovery Score':<20} {'False Detection Rate':<25} {'False Detection Score':<25} {'Efficiency Score':<20}"
    )
    print("-" * 130)

    # 打印每个缺陷类型的详细得分
    for defect_type, details in score_details.items():
        print(
            f"{defect_type:<20} {details['discovery_rate']:<20.2f} {details['discovery_score']:<20.2f} {details['false_detection_rate']:<25.2f} {details['false_detection_score']:<25} {details['efficiency_score']:<20}"
        )

    # 打印总分
    print("\nTotal Score:", total_score)


gt_data = parse_gt_folder(gt_folder_path)
# generate_mock_predictions(gt_data, "inferece.json")
predict_data = process_user_input(user_folder_path)

matched_gt, matched_preds, unmatched_preds = match_predictions(gt_data, predict_data)

matched_gt, matched_preds, unmatched_preds = group_by_defect_type(
    matched_gt, matched_preds, unmatched_preds
)

single_item_scores, score_details = calculate_single_item_scores(
    matched_gt, matched_preds, unmatched_preds, run_time, gt_data
)

total_score = calculate_total_score(single_item_scores)

print_formatted_scores(score_details, total_score)
