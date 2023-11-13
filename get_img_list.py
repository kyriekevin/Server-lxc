import os


def save_image_filenames_to_txt(folder_path, output_file):
    image_extensions = [".jpg", ".jpeg", ".png"]

    with open(output_file, "w") as file:
        for filename in os.listdir(folder_path):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                full_path = os.path.join(folder_path, filename)
                file.write(full_path + "\n")


save_image_filenames_to_txt("/Users/zhongyuzhe/00", "output.txt")
