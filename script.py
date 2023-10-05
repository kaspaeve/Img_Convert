import os
from PIL import Image
import tkinter as tk
from tkinter import filedialog
from tqdm import tqdm
import logging

def setup_logging():
    logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                        format='%(asctime)s - %(levelname)s - %(message)s')

def convert_and_resize_images(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    files = [f for f in os.listdir(input_dir) if f.endswith('.jpg')]
    
    for file in tqdm(files, desc='Processing images'):
        input_path = os.path.join(input_dir, file)
        output_path = os.path.join(output_dir, os.path.splitext(file)[0] + '.webp')
        
        try:
            with Image.open(input_path) as img:
                try:
                    resized_img = img.resize((1440, 1920), Image.LANCZOS)  # Updated dimensions here
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

def get_directory_path(prompt):
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    dir_path = filedialog.askdirectory(title=prompt)
    return dir_path

if __name__ == '__main__':
    setup_logging()
    input_dir = get_directory_path('Select Input Directory')
    output_dir = get_directory_path('Select Output Directory')
    
    if input_dir and output_dir:
        try:
            convert_and_resize_images(input_dir, output_dir)
        except Exception as e:
            error_message = f'An error occurred: {e}'
            print(error_message)
            logging.error(error_message)
    else:
        error_message = 'No directory selected. Exiting.'
        print(error_message)
        logging.error(error_message)
