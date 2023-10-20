import os
import json
from PIL import Image, ImageTk, ExifTags
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Label, Button, Menu
from tkinter.ttk import Frame, Progressbar, Separator 
from ttkthemes import ThemedTk
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

def save_last_selected_dirs(input_dir, output_dir):
    with open('config.json', 'w') as f:
        json.dump({'input_dir': input_dir, 'output_dir': output_dir}, f)

def get_last_selected_dirs():
    try:
        with open('config.json', 'r') as f:
            dirs = json.load(f)
            return dirs['input_dir'], dirs['output_dir']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None, None

def update_directory_path(label, title, input_label, output_label):
    dir_path = filedialog.askdirectory(title=title)
    if dir_path:
        label.config(text=dir_path)
        save_last_selected_dirs(input_label.cget("text"), output_label.cget("text"))
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

def convert_and_resize_images(input_dir, output_dir, batch_mode, terminal, progress, file_progress, resolution_choice, custom_width, custom_height):
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
                file_progress['value'] = 0
                message = f'{file} ({img.width}x{img.height}) converted to ({resized_img.width}x{resized_img.height}) processed successfully.'
                print(message)
                print_to_terminal(terminal, message)
                file_progress['value'] = 100
        except IOError as e:
            error_message = f'Error processing {file}: {e}'
            print(error_message)
            print_to_terminal(terminal, error_message)
            logging.error(error_message)
            file_progress['value'] = 100

def on_convert_click(input_label, output_label, terminal, progress, file_progress, resolution_choice, width_entry, height_entry):
    input_dir = input_label.cget("text")
    output_dir = output_label.cget("text")
    batch_mode = resolution_choice.get() == "Automatically"

    if input_dir and output_dir:
        try:
            progress['value'] = 0  
            file_progress['value'] = 0
            convert_and_resize_images(input_dir, output_dir, batch_mode, terminal, progress, file_progress, resolution_choice.get(), width_entry.get(), height_entry.get())
        except Exception as e:
            error_message = f'An error occurred: {e}'
            print_to_terminal(terminal, error_message)
            logging.error(error_message)
    else:
        error_message = 'No directory selected. Exiting.'
        print_to_terminal(terminal, error_message)
        logging.error(error_message)

def update_entry_visibility(resolution_choice, width_entry, height_entry):
    if resolution_choice.get() == "Custom":
        width_entry.pack(side='left', expand=True, fill='x', padx=5, pady=5)  
        height_entry.pack(side='left', expand=True, fill='x', padx=5, pady=5)  
    else:
        width_entry.pack_forget()  #
        height_entry.pack_forget()  



def initialize_gui():
    root = ThemedTk(theme="equilux")
    root.title("Image Converter")

    menu = Menu(root)
    help_menu = Menu(menu, tearoff=0)
    help_menu.add_command(label="Documentation", command=open_documentation)
    menu.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menu)

    main_frame = Frame(root, padding="10")
    main_frame.grid(sticky=(tk.E, tk.W, tk.N, tk.S), padx=10, pady=10)

    input_frame = Frame(main_frame)
    input_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

    input_button = tk.Button(input_frame, text='Input Directory', command=lambda: update_directory_path(input_label, 'Input Directory', input_label, output_label))
    input_button.grid(row=0, column=0)

    input_label = tk.Label(input_frame, text='Not selected', font=("Helvetica", 12), anchor='w')
    input_label.grid(row=0, column=1, sticky='ew')

    output_frame = Frame(root)
    output_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)

    output_button = tk.Button(output_frame, text='Output Directory', command=lambda: update_directory_path(output_label, 'Output Directory', input_label, output_label))
    output_button.grid(row=0, column=0)

    output_label = tk.Label(output_frame, text='Not selected', font=("Helvetica", 12), anchor='w')
    output_label.grid(row=0, column=1, sticky='ew')

    resolution_choice = tk.StringVar(value="Automatically")
    auto_radio = tk.Radiobutton(root, text="Recommended dimensions", variable=resolution_choice, value="Automatically",
                                command=lambda: update_entry_visibility(resolution_choice, width_entry, height_entry))
    auto_radio.grid(row=2, columnspan=3, sticky='w', padx=20)
    custom_radio = tk.Radiobutton(root, text="Specify dimensions", variable=resolution_choice, value="Custom",
                                  command=lambda: update_entry_visibility(resolution_choice, width_entry, height_entry))
    custom_radio.grid(row=3, column=0, sticky='w', padx=20)

    dimension_frame = Frame(root)  
    dimension_frame.grid(row=4, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

    width_frame = Frame(dimension_frame)  
    width_frame.pack(fill='x', padx=5, pady=5)  

    width_label = tk.Label(width_frame, text="Width:")  
    width_label.pack(side='left') 

    width_entry = tk.Entry(width_frame)  
    width_entry.pack(side='left', expand=True, fill='x')  
    height_frame = Frame(dimension_frame)  
    height_frame.pack(fill='x', padx=5, pady=5)  

    height_label = tk.Label(height_frame, text="Height:")  
    height_label.pack(side='left')  

    height_entry = tk.Entry(height_frame)  
    height_entry.pack(side='left', expand=True, fill='x')  

    # Initially hide the entries
    width_entry.grid_remove()
    height_entry.grid_remove()

    convert_button = tk.Button(root, text="Convert", command=lambda: on_convert_click(input_label, output_label, terminal, progress, file_progress, resolution_choice, width_entry, height_entry))
    convert_button.grid(row=7, columnspan=5, pady=10)

    terminal = ScrolledText.ScrolledText(main_frame, state='disabled', width=80, height=20, wrap='word', fg='black', bg='white')
    terminal.grid(row=6, column=0, columnspan=5, padx=5, pady=5, sticky='ew')

    progress = Progressbar(main_frame, orient='horizontal', length=400, mode='determinate')
    progress.grid(row=7, column=0, columnspan=5, padx=5, pady=5, sticky='ew')

    file_progress = Progressbar(main_frame, orient='horizontal', length=400, mode='determinate')
    file_progress.grid(row=8, column=0, columnspan=5, padx=5, pady=5, sticky='ew')

    for col in range(5):
        main_frame.grid_columnconfigure(col, weight=1)
    main_frame.grid_rowconfigure(6, weight=1)  # Make the terminal resizable


    # Load last selected directories
    input_dir, output_dir = get_last_selected_dirs()
    if input_dir and output_dir:
        input_label.config(text=input_dir)
        output_label.config(text=output_dir)

    root.mainloop()

def open_documentation():
    # Open your documentation file or webpage
    pass

if __name__ == '__main__':
    try:
        setup_logging()
        initialize_gui()
    except Exception as e:
        print(f"Exception: {e}")
        logging.exception(e)
