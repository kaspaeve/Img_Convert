import os
from PIL import Image, ImageTk, ExifTags
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Toplevel, Label, Button
from tqdm import tqdm
import logging

def setup_logging():
    logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

def correct_image_orientation(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif_data = img._getexif()
        if exif_data is not None and orientation in exif_data:
            orientation_value = exif_data[orientation]
            if orientation_value == 2:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation_value == 3:
                img = img.rotate(180)
            elif orientation_value == 4:
                img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation_value == 5:
                img = img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation_value == 6:
                img = img.rotate(-90, expand=True)
            elif orientation_value == 7:
                img = img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return img

def get_optimal_resolutions(original_size):
    common_widths = [1920, 1440, 1280]
    original_width, original_height = original_size
    aspect_ratio = original_width / original_height
    return [(int(width), int(width / aspect_ratio)) for width in common_widths]

def select_resolution(image_name, img_path, resolutions):
    selected_resolution = None

    def on_select(res):
        nonlocal selected_resolution
        selected_resolution = res
        root.destroy()

    def on_skip():
        nonlocal selected_resolution
        selected_resolution = 'SKIP'
        root.destroy()

    root = Toplevel()
    root.title(f"Select resolution for {image_name}")

    with Image.open(img_path) as img:
        img.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(img)
        image_label = Label(root, image=photo)
        image_label.image = photo
        image_label.pack(pady=10)

    Label(root, text=image_name).pack(pady=10)
    Label(root, text="Select the optimal resolution:").pack(pady=10)

    for res in resolutions:
        btn = Button(root, text=f"{res[0]} x {res[1]}", command=lambda r=res: on_select(r))
        btn.pack(pady=5)

    skip_button = Button(root, text="Skip", command=on_skip)
    skip_button.pack(pady=10)

    root.mainloop()

    return selected_resolution

def batch_processing_choice():
    root = tk.Tk()
    root.withdraw()
    return messagebox.askyesno("Batch Processing", "Do you want to batch process all images with automatically determined resolutions? If No, you'll select resolutions for each image manually.")

def convert_and_resize_images(input_dir, output_dir, batch_mode):
    os.makedirs(output_dir, exist_ok=True)
    files = [f for f in os.listdir(input_dir) if f.endswith('.jpg')]

    for file in tqdm(files, desc='Processing images'):
        input_path = os.path.join(input_dir, file)
        output_path = os.path.join(output_dir, os.path.splitext(file)[0] + '.webp')

        try:
            with Image.open(input_path) as img:
                img = correct_image_orientation(img)  # Correct orientation before any other operations

                if not batch_mode:
                    resolutions = get_optimal_resolutions(img.size)
                    chosen_resolution = select_resolution(file, input_path, resolutions)
                    if chosen_resolution == 'SKIP':
                        print(f"{file} was skipped by the user.")
                        continue
                else:
                    chosen_resolution = get_optimal_resolutions(img.size)[0]

                resized_img = img.resize(chosen_resolution, Image.LANCZOS)
                resized_img.save(output_path, 'WEBP')
                print(f'{file} processed successfully.')
        except Exception as e:
            error_message = f'Error processing {file}: {e}'
            print(error_message)
            logging.error(error_message)

def get_directory_path(prompt):
    root = tk.Tk()
    root.withdraw()
    dir_path = filedialog.askdirectory(title=prompt)
    return dir_path

if __name__ == '__main__':
    setup_logging()
    input_dir = get_directory_path('Select Input Directory')
    output_dir = get_directory_path('Select Output Directory')

    if input_dir and output_dir:
        batch_mode = batch_processing_choice()
        try:
            convert_and_resize_images(input_dir, output_dir, batch_mode)
        except Exception as e:
            error_message = f'An error occurred: {e}'
            print(error_message)
            logging.error(error_message)
    else:
        error_message = 'No directory selected. Exiting.'
        print(error_message)
        logging.error(error_message)
