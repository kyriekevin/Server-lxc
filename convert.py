import json
import os


def convert_polygons_to_rects(step_1_data):
    rects = []

    for polygon_data in step_1_data["result"]:
        polygon = polygon_data["pointList"]
        min_x = min(point["x"] for point in polygon)
        max_x = max(point["x"] for point in polygon)
        min_y = min(point["y"] for point in polygon)
        max_y = max(point["y"] for point in polygon)

        rects.append(
            {
                "x": min_x,
                "y": min_y,
                "width": max_x - min_x,
                "height": max_y - min_y,
                "attribute": polygon_data["attribute"],
                "valid": polygon_data["valid"],
                "id": polygon_data["id"],
                "sourceID": polygon_data["sourceID"],
                "textAttribute": polygon_data["textAttribute"],
                "order": polygon_data["order"],
            }
        )

    return {"toolName": "rectTool", "result": rects}


def process_json_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r") as file:
                data = json.load(file)

            if data["step_1"]["toolName"] == "polygonTool":
                data["step_1"] = convert_polygons_to_rects(data["step_1"])
                new_file_path = os.path.join(folder_path, filename)
                with open(new_file_path, "w") as new_file:
                    json.dump(data, new_file, indent=4)


process_json_files("./00/")
