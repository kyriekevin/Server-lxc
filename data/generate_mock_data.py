import os
import json
import random
from typing import Dict, List, Tuple

gt_folder = "./img_test/"
mock_data_folder = "mock_data"


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


def generate_individual_mock_jsons(gt_data, mock_data_folder):
    if not os.path.exists(mock_data_folder):
        os.makedirs(mock_data_folder)

    for image_file_name, objects in gt_data.items():
        mock_objects = []
        for obj in objects:
            # choice = random.random()
            # if choice < 0.8:
            #     mock_obj = {
            #         "x": obj["x"] + random.randint(-10, 10),
            #         "y": obj["y"] + random.randint(-10, 10),
            #         "width": obj["width"] + random.randint(-10, 10),
            #         "height": obj["height"] + random.randint(-10, 10),
            #         "attribute": obj["attribute"],
            #     }
            #     mock_objects.append(mock_obj)
            mock_obj = {
                "x": obj["x"],
                "y": obj["y"],
                "width": obj["width"],
                "height": obj["height"],
                "attribute": obj["attribute"],
            }
            mock_objects.append(mock_obj)

        # 随机生成一些额外的对象
        # extra_predictions_rate = random.randint(0, 10)
        # for _ in range(extra_predictions_rate):
        #     mock_obj = {
        #         "x": random.randint(0, 1000),
        #         "y": random.randint(0, 1000),
        #         "width": random.randint(10, 1000),
        #         "height": random.randint(10, 1000),
        #         "attribute": obj["attribute"],
        #     }
        #     mock_objects.append(mock_obj)

        mock_data = {"image_name": image_file_name, "objects": mock_objects}

        # 写入模拟数据到文件
        output_file_path = os.path.join(mock_data_folder, image_file_name + ".json")
        with open(output_file_path, "w", encoding="utf-8") as file:
            json.dump(mock_data, file, indent=4, ensure_ascii=False)


gt_data = parse_gt_folder(gt_folder)
generate_individual_mock_jsons(gt_data, mock_data_folder)
