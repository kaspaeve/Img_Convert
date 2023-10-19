import os
from PIL import Image, ImageTk, ExifTags
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Label, Button
from tkinter.ttk import Progressbar
from ttkthemes import ThemedTk
from tqdm import tqdm
import logging
import tkinter.scrolledtext as ScrolledText


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

def update_directory_path(label, title):
    dir_path = filedialog.askdirectory(title=title) 
    if dir_path:
        label.config(text=f'{title}: {dir_path}')
    return dir_path

def print_to_terminal(terminal, message):
    terminal.config(state='normal')
    tag = None
    if "successfully" in message:
        tag = "Success"
        terminal.tag_config(tag, foreground='green')
    elif "Error" in message or "error" in message:
        tag = "Error"
        terminal.tag_config(tag, foreground='red')
    terminal.insert(tk.END, message + '\n', tag)
    terminal.config(state='disabled')
    terminal.see(tk.END)

def convert_and_resize_images(input_dir, output_dir, batch_mode, terminal, progress, file_progress):  # Added file_progress argument
    os.makedirs(output_dir, exist_ok=True)
    files = [f for f in os.listdir(input_dir) if f.endswith('.jpg')]
    total_files = len(files)
    processed_files = 0

    for file in files:
        input_path = os.path.join(input_dir, file)
        output_path = os.path.join(output_dir, os.path.splitext(file)[0] + '.webp')

        try:
            with Image.open(input_path) as img:
                img = correct_image_orientation(img)  

                if not batch_mode:
                    resolutions = get_optimal_resolutions(img.size)
                    chosen_resolution = select_resolution(file, input_path, resolutions)
                    if chosen_resolution == 'SKIP':
                        message = f"{file} was skipped by the user."
                        print(message)
                        print_to_terminal(terminal, message)
                        file_progress['value'] = 100  
                        continue
                else:
                    chosen_resolution = get_optimal_resolutions(img.size)[0]

                resized_img = img.resize(chosen_resolution, Image.LANCZOS)
                resized_img.save(output_path, 'WEBP')
                processed_files += 1  
                progress['value'] = (processed_files / total_files) * 100
                file_progress['value'] = 0  #
                message = f'{file} processed successfully.'
                print(message)
                print_to_terminal(terminal, message)
                file_progress['value'] = 100  
        except IOError as e:
            error_message = f'Error processing {file}: {e}'
            print(error_message)
            print_to_terminal(terminal, error_message)
            logging.error(error_message)
            file_progress['value'] = 100

def get_directory_path(prompt):
    root = tk.Tk()
    root.withdraw()
    dir_path = filedialog.askdirectory(title=prompt)
    return dir_path

def on_convert_click(input_label, output_label, terminal, progress, file_progress):
    input_dir = update_directory_path(input_label, 'Select Input Directory')
    output_dir = update_directory_path(output_label, 'Select Output Directory')

    if input_dir and output_dir:
        batch_mode = batch_processing_choice()
        try:
            progress['value'] = 0  
            file_progress['value'] = 0
            convert_and_resize_images(input_dir, output_dir, batch_mode, terminal, progress, file_progress)
        except Exception as e:
            error_message = f'An error occurred: {e}'
            print_to_terminal(terminal, error_message)
            logging.error(error_message)
    else:
        error_message = 'No directory selected. Exiting.'
        print_to_terminal(terminal, error_message)
        logging.error(error_message)

def initialize_gui():
    root = ThemedTk(theme="equilux")
    root.title("Image Converter")

    input_label = tk.Button(root, text='Input Directory: Not selected', font=("Helvetica", 12), anchor='w',
                            command=lambda: update_directory_path(input_label, 'Input Directory'))  # Changed Label to Button
    input_label.pack(fill='x', padx=5, pady=5)

    output_label = tk.Button(root, text='Output Directory: Not selected', font=("Helvetica", 12), anchor='w',
                             command=lambda: update_directory_path(output_label, 'Output Directory'))  # Changed Label to Button
    output_label.pack(fill='x', padx=5, pady=5)

    convert_button = tk.Button(root, text="Convert", command=lambda: on_convert_click(input_label, output_label, terminal, progress, file_progress))
    convert_button.pack(pady=10)

    terminal = ScrolledText.ScrolledText(root, state='disabled', width=80, height=20, wrap='word', fg='white', bg='black')
    terminal.pack()

    progress = Progressbar(root, orient='horizontal', length=400, mode='determinate')
    progress.pack(pady=5)

    file_progress = Progressbar(root, orient='horizontal', length=400, mode='determinate')
    file_progress.pack(pady=5)

    root.mainloop()


if __name__ == '__main__':
    setup_logging()
    initialize_gui() 
