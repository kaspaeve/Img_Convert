import os
from PIL import Image
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from tqdm import tqdm
import logging

def setup_logging():
    logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

def convert_and_resize_images(input_dir, output_dir, dimensions):
    os.makedirs(output_dir, exist_ok=True)
    
    files = [f for f in os.listdir(input_dir) if f.endswith('.jpg')]
    
    for file in tqdm(files, desc='Processing images'):
        input_path = os.path.join(input_dir, file)
        output_path = os.path.join(output_dir, os.path.splitext(file)[0] + '.webp')
        
        try:
            with Image.open(input_path) as img:
                original_width, original_height = img.size
                original_aspect_ratio = original_width / original_height

                # Adjust dimensions based on the original aspect ratio
                new_width, new_height = adjust_dimensions(original_aspect_ratio, dimensions)

                try:
                    resized_img = img.resize((new_width, new_height), Image.LANCZOS)  
                    resized_img.save(output_path, 'WEBP')
                    print(f'{file} processed successfully.')
                except Exception as e:
                    error_message = f'Error resizing or saving {file}: {e}'
                    print(error_message)
                    logging.error(error_message)
        except Exception as e:
            error_message = f'Error opening {file}: {e}'
            print(error_message)
            logging.error(error_message)

def adjust_dimensions(original_aspect_ratio, dimensions):
    width, height = dimensions
    common_ratios = [(4, 3), (16, 9)]
    closest_ratio = min(common_ratios, key=lambda x: abs(original_aspect_ratio - x[0]/x[1]))
    new_width = int(height * (closest_ratio[0] / closest_ratio[1]))
    new_height = int(width / (closest_ratio[0] / closest_ratio[1]))
    return new_width, new_height  # You may want to decide between new_width x height or width x new_height based on some criteria

def get_directory_path(prompt):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    dir_path = filedialog.askdirectory(title=prompt)
    return dir_path

def get_image_dimensions():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    width = simpledialog.askinteger("Input", "Enter the width:")
    height = simpledialog.askinteger("Input", "Enter the height:")
    
    if width and height:
        if not confirm_aspect_ratio(width, height):
            return None
        if not confirm_proceed():
            return None
    
    return (width, height)

def confirm_aspect_ratio(width, height):
    aspect_ratio = width / height
    common_ratios = [(4, 3), (16, 9)]
    closest_ratio = min(common_ratios, key=lambda x: abs(aspect_ratio - x[0]/x[1]))
    recommended_width = int(height * (closest_ratio[0] / closest_ratio[1]))
    recommended_height = int(width / (closest_ratio[0] / closest_ratio[1]))
    
    warning_message = (
        f"The provided dimensions ({width}x{height}) will change the aspect ratio, "
        f"which might result in image distortion. "
        f"It's recommended to resize to either {recommended_width}x{height} "
        f"or {width}x{recommended_height} to maintain a common aspect ratio of "
        f"{closest_ratio[0]}:{closest_ratio[1]}. Are you sure you want to proceed?"
    )
    return messagebox.askokcancel("Warning", warning_message)

def confirm_proceed():
    return messagebox.askokcancel("Confirmation", "Are you sure you want to proceed with these dimensions?")

if __name__ == '__main__':
    setup_logging()
    input_dir = get_directory_path('Select Input Directory')
    output_dir = get_directory_path('Select Output Directory')
    
    if input_dir and output_dir:
        dimensions = get_image_dimensions()
        if dimensions:
            try:
                convert_and_resize_images(input_dir, output_dir, dimensions)
            except Exception as e:
                error_message = f'An error occurred: {e}'
                print(error_message)
                logging.error(error_message)
        else:
            error_message = 'No dimensions provided or user cancelled. Exiting.'
            print(error_message)
            logging.error(error_message)
    else:
        error_message = 'No directory selected. Exiting.'
        print(error_message)
        logging.error(error_message)
