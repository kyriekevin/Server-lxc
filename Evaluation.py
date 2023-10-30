import argparse
import os


def read_txt_file(file_path, expected_folder_path):
    result_dict = {}
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                image_name, label = line.strip().split(" ")
                folder_path = os.path.dirname(image_name)

                if folder_path != expected_folder_path:
                    print(
                        f"Folder path mismatch: Expected {expected_folder_path}, got {folder_path}"
                    )
                    return None

                result_dict[image_name] = int(label)

    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return result_dict


def calculate_precision_recall(gt, inference):
    tp = 0  # True Positive
    fp = 0  # False Positive
    fn = 0  # False Negative
    unmatched_images = []  # List to store unmatched images

    for img, label in gt.items():
        if img in inference:
            if label == inference[img]:
                tp += 1
            else:
                fp += 1
                fn += 1
        else:
            fn += 1
            unmatched_images.append(img)

    for img in inference:
        if img not in gt:
            fp += 1
            unmatched_images.append(img)

    precision = tp / (tp + fp) if tp + fp != 0 else 0
    recall = tp / (tp + fn) if tp + fn != 0 else 0

    return precision, recall, unmatched_images


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate the precision and recall based on gt.txt and inference.txt"
    )
    parser.add_argument(
        "gt_txt_path", type=str, help="Path to the ground truth txt file."
    )
    parser.add_argument(
        "inference_txt_path", type=str, help="Path to the inference txt file."
    )
    parser.add_argument("image_folder_path", type=str, help="Path to the image folder.")

    args = parser.parse_args()

    gt = read_txt_file(args.gt_txt_path, args.image_folder_path)
    inference = read_txt_file(args.inference_txt_path, args.image_folder_path)

    if gt is None or inference is None:
        print("Terminating due to folder path mismatch.")
        exit(1)

    precision, recall, unmatched_images = calculate_precision_recall(gt, inference)

    if unmatched_images:
        print("Warning: The following images were not matched in both files:")
        for img in unmatched_images:
            print(img)

    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
