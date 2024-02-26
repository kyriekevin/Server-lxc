import random
import os


def rename_files_in_subfolders_randomly(main_folder):
    # List to store all file names
    all_files = []

    # Collect all file names
    for subfolder in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder)

        # Proceed only if it's a directory
        if os.path.isdir(subfolder_path):
            original_folder = os.path.join(subfolder_path, "原图")
            json_folder = os.path.join(subfolder_path, "json")

            if os.path.exists(original_folder):
                for file_name in os.listdir(original_folder):
                    if file_name.endswith(".jpg"):
                        all_files.append(
                            (
                                os.path.join(original_folder, file_name),
                                os.path.join(json_folder, file_name + ".json"),
                            )
                        )

    # Shuffle the list for randomization
    random.shuffle(all_files)

    # Rename files with a unique ID
    cnt = 0
    for id, (original_file, json_file) in enumerate(all_files):
        new_file_name = f"{str(id).zfill(6)}.jpg"
        new_json_file_name = f"{str(id).zfill(6)}.json"

        os.rename(
            original_file, os.path.join(os.path.dirname(original_file), new_file_name)
        )

        if os.path.exists(json_file):
            os.rename(
                json_file, os.path.join(os.path.dirname(json_file), new_json_file_name)
            )
            cnt += 1
        else:
            print(original_file)
            print()

    return f"Renaming completed. Total files renamed: {cnt}"


# Example usage
# Note: Replace 'main_folder_path' with the actual path of the main folder to be processed.
main_folder_path = "./img_test/"
result = rename_files_in_subfolders_randomly(main_folder_path)
print(result)
