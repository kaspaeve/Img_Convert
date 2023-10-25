import os
import json
from PIL import Image, ImageTk, ExifTags
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Label, Button, Menu
from tkinter.ttk import Frame, Progressbar
from ttkthemes import ThemedTk
import logging
import tkinter.scrolledtext as ScrolledText
import threading

logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ImageConverter:
    def __init__(self, config):
        self.is_converting = threading.Event()
        self.current_file_index = 0
        self.stop_event = threading.Event()
        self.stats = ConversionStats(config)
        self.load_stats()

    def load_stats(self):
        self.stats.load_stats()

    def setup_logging(self):
        logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def correct_image_orientation(self, img):
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
        except (AttributeError, KeyError, IndexError) as e:
            logging.exception(e)  
        return img

import json

class ConversionStats:
    def __init__(self, config):
        self.total_files_converted = config.get('total_files_converted', 0)
        self.total_space_saved = config.get('total_space_saved', 0)  # in bytes

    def update_stats(self, old_size, new_size):
        self.total_files_converted += 1
        self.total_space_saved += old_size - new_size

    def get_stats(self):
        return {
            'total_files_converted': self.total_files_converted,
            'total_space_saved': self.total_space_saved
        }


    def load_stats(self):
        try:
            with open('config.json', 'r') as file:
                data = json.load(file)
                self.total_files_converted = data['total_files_converted']
                self.total_space_saved = data['total_space_saved']
        except FileNotFoundError:
            pass  
        except json.JSONDecodeError:
            print("Could not decode the stats file. Starting with fresh stats.")



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

def save_last_selected_dirs(input_dir, output_dir, converter):
    config = {
        'input_dir': input_dir,
        'output_dir': output_dir,
        'total_files_converted': converter.stats.total_files_converted,
        'total_space_saved': converter.stats.total_space_saved,
    }
    try:
        with open('config.json', 'w') as file:
            json.dump(config, file)
    except Exception as e:
        logging.exception(e)



def get_last_selected_dirs():
    try:
        with open('config.json', 'r') as file:
            data = json.load(file)
            input_dir = data.get('input_dir', '')
            output_dir = data.get('output_dir', '')
            config = {
                'total_files_converted': data.get('total_files_converted', 0),
                'total_space_saved': data.get('total_space_saved', 0),
            }
            return input_dir, output_dir, config
    except FileNotFoundError:
        print("Config file not found. Starting with fresh directories and config.")
        return '', '', {'total_files_converted': 0, 'total_space_saved': 0}
    except json.JSONDecodeError:
        print("Could not decode the config file. Starting with fresh directories and config.")
        return '', '', {'total_files_converted': 0, 'total_space_saved': 0}



def update_image_count_label(output_dir, image_count_label):
    try:
        files = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
        image_count = len(files)
        image_count_label.config(text=f"{image_count} images currently selected in batch.")
    except Exception as e:
        logging.exception(e)

def update_directory_path(title, input_label_text, output_label_text, image_count_label=None):
    dir_path = filedialog.askdirectory(title=title)
    if dir_path:
        if title == 'Input Directory':
            input_label_text.set(dir_path)  
        else:
            output_label_text.set(dir_path)  
        save_last_selected_dirs(input_label_text.get(), output_label_text.get(), converter)  
        if image_count_label:
            update_image_count_label(dir_path, image_count_label)
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

def convert_and_resize_images(converter, input_dir, output_dir, batch_mode, terminal, progress, resolution_choice, custom_width, custom_height, progress_text, stop_button, resume_button, root):
    if converter.is_converting.is_set():
        print_to_terminal(terminal, "A conversion process is already running.")
        return
    converter.is_converting.set()
    try:
        
        os.makedirs(output_dir, exist_ok=True)
        files = [f for f in os.listdir(input_dir) if f.endswith('.jpg')]
        total_files = len(files)
        processed_files = 0  

        for i, file in enumerate(files[converter.current_file_index:], start=converter.current_file_index):
            converter.current_file_index = i
            if converter.stop_event.is_set() or not converter.is_converting.is_set():
                print_to_terminal(terminal, "Process was stopped.")
                converter.current_file_index = i
                return
            input_path = os.path.join(input_dir, file)
            output_path = os.path.join(output_dir, os.path.splitext(file)[0] + '.webp')
            processed_files += 1  
            progress_value = (processed_files / total_files) * 100
            progress['value'] = progress_value
            
            progress_text.config(text=f"{processed_files}/{total_files} - {progress_value:.0f}%")
            root.update_idletasks()  
            old_size = os.path.getsize(input_path)
            try:
                with Image.open(input_path) as img:
                    img = converter.correct_image_orientation(img)  

                    if not batch_mode:
                        resolutions = get_optimal_resolutions(img.size)
                        chosen_resolution = select_resolution(file, input_path, resolutions)
                        if chosen_resolution == 'SKIP':
                            message = f"{file} was skipped by an unknown force."
                            print(message)
                            print_to_terminal(terminal, message)
                            
                            continue
                    else:
                        chosen_resolution = get_optimal_resolutions(img.size)[0]

                    resized_img = img.resize(chosen_resolution, Image.LANCZOS)
                    resized_img.save(output_path, 'WEBP')
                    new_size = os.path.getsize(output_path)
                    converter.stats.update_stats(old_size, new_size)
                    progress['value'] = (processed_files / total_files) * 100 
                    root.update_idletasks()
                    
                    message = f'{file} ({img.width}x{img.height}) converted to ({resized_img.width}x{resized_img.height}) processed successfully.'
                    print(message)
                    print_to_terminal(terminal, message)
                    
            except IOError as e:
                error_message = f'Error processing {file}: {e}'
                print(error_message)
                print_to_terminal(terminal, error_message)
                logging.error(error_message)
                
                stop_button.grid_remove()

    except Exception as e:
        error_message = f'An error occurred: {e}'
        print(error_message)
        print_to_terminal(terminal, error_message)
        logging.error(error_message)
    finally: 
        save_last_selected_dirs(input_dir, output_dir, converter)
        converter.is_converting.clear()
        stop_button.grid_remove()
        resume_button.grid_remove()
        logging.info("Conversion process stopped or completed.") 


def on_stop_click(converter):
    
    converter.is_converting.clear()
    converter.stop_event.set()
    logging.info("Stop button clicked.")

def on_convert_click(converter, input_label_text, output_label_text, terminal, progress, resolution_choice, width_entry, height_entry, progress_text, stop_button, root):
    if converter.is_converting.is_set():
        print_to_terminal(terminal, "A conversion process is already running.")
        return
    converter.stop_event.clear()
    converter.current_file_index = 0 
    input_dir = input_label_text.get()
    output_dir = output_label_text.get()
    save_last_selected_dirs(input_dir, output_dir, converter)
    batch_mode = resolution_choice.get() == "Automatically"

    if input_dir and output_dir:
        stop_button.grid(row=10, columnspan=5, pady=10)
        resume_button.grid(row=10, columnspan=5, pady=10)
        threading.Thread(target=convert_and_resize_images, args=(converter, input_dir, output_dir, batch_mode, terminal, progress, resolution_choice.get(), width_entry.get(), height_entry.get(), progress_text, stop_button, resume_button, root)).start()
    else:
        error_message = 'No directory selected. Exiting.'
        print_to_terminal(terminal, error_message)
        logging.error(error_message)
    

def on_resume_click(converter, input_label, output_label, terminal, progress, resolution_choice, width_entry, height_entry, progress_text, stop_button, root):
    if converter.is_converting.is_set():
        print_to_terminal(terminal, "A conversion process is already running.")
        return
    converter.stop_event.clear()
    converter.is_converting.set()
    input_dir = input_label.cget("text")
    output_dir = output_label.cget("text")
    batch_mode = resolution_choice.get() == "Automatically"

    if input_dir and output_dir:
        stop_button.grid(row=10, columnspan=5, pady=10)
        threading.Thread(target=convert_and_resize_images, args=(converter, input_dir, output_dir, batch_mode, terminal, progress, resolution_choice.get(), width_entry.get(), height_entry.get(), progress_text, stop_button, resume_button, root)).start()

    else:
        error_message = 'No directory selected. Exiting.'
        print_to_terminal(terminal, error_message)
        logging.error(error_message)



def show_about_window(converter):
    about_window = Toplevel()
    about_window.title("About")
    
    frame = Frame(about_window)  
    frame.pack(fill='both', expand=True, padx=10, pady=10)  

    author_label = Label(frame, text="Author: Austin Scheller", anchor='w', justify='left', width=50)  
    author_label.grid(sticky='w', row=0, column=0, padx=5, pady=5)  

    email_label = Label(frame, text="Email: austinscheller1@gmail.com", anchor='w', justify='left', width=50)
    email_label.grid(sticky='w', row=1, column=0, padx=5, pady=5)

    files_label = Label(frame, text=f"Total Files Converted: {converter.stats.total_files_converted}", anchor='w', justify='left', width=50)
    files_label.grid(sticky='w', row=2, column=0, padx=5, pady=5)

    space_saved_label = Label(frame, text=f"Space Saved: {converter.stats.total_space_saved / (1024 * 1024):.2f} MB", anchor='w', justify='left', width=50)
    space_saved_label.grid(sticky='w', row=3, column=0, padx=5, pady=5)

    about_window.mainloop()


def update_entry_visibility(resolution_choice, dimension_frame):
    if resolution_choice.get() == "Custom":
        dimension_frame.grid()
    else:
        dimension_frame.grid_remove()

def initialize_gui():
    global converter  
    global resume_button 


    input_dir, output_dir, config = get_last_selected_dirs()
    converter = ImageConverter(config) 
    converter.setup_logging() 

    root = ThemedTk(theme="Breeze")
    root.title("Image Converter")
    root.iconbitmap('icons/icon.ico')

    global input_label_text 
    global output_label_text

    input_label_text = tk.StringVar() 
    output_label_text = tk.StringVar()

    menu = Menu(root)
    help_menu = Menu(menu, tearoff=0)
    help_menu.add_command(label="Documentation", command=open_documentation)
    menu.add_cascade(label="Help", menu=help_menu)
    root.config(menu=menu)

    about_menu = Menu(menu, tearoff=0)
    about_menu.add_command(label="About", command=lambda: show_about_window(converter))
    menu.add_cascade(label="About", menu=about_menu)

    main_frame = Frame(root, padding="10")
    main_frame.grid(sticky=(tk.E, tk.W, tk.N, tk.S), padx=10, pady=10)

    input_frame = Frame(main_frame)
    input_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

    input_icon = ImageTk.PhotoImage(Image.open('icons/input_icon.png'))
    input_button = tk.Button(input_frame, image=input_icon, compound=tk.LEFT, command=lambda: update_directory_path('Input Directory', input_label_text, output_label_text))
    input_button.grid(row=0, column=0)

    input_label = tk.Label(input_frame, text=input_dir)
    input_label.grid(row=0, column=1)
    

    arrow_label = tk.Label(input_frame, text=' > ', font=("Helvetica", 12))
    arrow_label.grid(row=0, column=2)

    output_icon = ImageTk.PhotoImage(Image.open('icons/output_icon.png'))
    output_button = tk.Button(input_frame, image=output_icon, compound=tk.LEFT, command=lambda: update_directory_path('Output Directory', input_label_text, output_label_text))
    output_button.grid(row=0, column=3)
    

    output_label = tk.Label(input_frame, text=output_dir)  
    output_label.grid(row=0, column=4)
    

    resolution_choice = tk.StringVar(value="Automatically")
    auto_radio = tk.Radiobutton(root, text="Recommended dimensions", variable=resolution_choice, value="Automatically",
    state='disabled')  
    auto_radio.grid(row=2, columnspan=3, sticky='w', padx=20)
    custom_radio = tk.Radiobutton(root, text="Specify dimensions", variable=resolution_choice, value="Custom",
    state='disabled')  
    custom_radio.grid(row=3, column=0, sticky='w', padx=20)

    dimension_frame = Frame(root)  
    dimension_frame.grid(row=4, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
    dimension_frame.grid_remove()  


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

    image_count_label = tk.Label(root, text="")
    image_count_label.grid(row=5, column=0, columnspan=5, pady=5, sticky='ew')

    convert_icon = ImageTk.PhotoImage(Image.open('icons/convert_icon.png'))
    convert_button = tk.Button(root, text="Convert", image=convert_icon, compound=tk.LEFT,
                           command=lambda: on_convert_click(converter, input_label_text, output_label_text, terminal, progress, resolution_choice, width_entry, height_entry, progress_text, stop_button, root))  

    convert_button.grid(row=7, columnspan=5, pady=10)

    terminal = ScrolledText.ScrolledText(main_frame, state='disabled', width=80, height=20, wrap='word', fg='green', bg='black', font=("Fixedsys", 12))
    terminal.grid(row=6, column=0, columnspan=5, padx=5, pady=5, sticky='ew')

    progress = Progressbar(main_frame, orient='horizontal', length=400, mode='determinate')
    progress.grid(row=8, column=0, columnspan=5, padx=5, pady=5, sticky='ew')  
    progress_text = tk.Label(main_frame, text="")
    progress_text.grid(row=7, column=0, columnspan=5, pady=5, sticky='ew') 
    


    for col in range(5):
        main_frame.grid_columnconfigure(col, weight=1)
    main_frame.grid_rowconfigure(6, weight=1)  

    button_frame = Frame(root)  
    button_frame.grid(row=10, columnspan=5, pady=10)  

    stop_icon = ImageTk.PhotoImage(Image.open('icons/stop_icon.png'))
    stop_button = tk.Button(button_frame, text="Stop", image=stop_icon, compound=tk.LEFT, command=lambda: on_stop_click(converter))
    stop_button.grid(row=0, column=0, padx=5)  

    

    resume_icon = ImageTk.PhotoImage(Image.open('icons/resume_icon.png'))
    resume_button = tk.Button(button_frame, text="Resume", image=resume_icon, compound=tk.LEFT, 
                              command=lambda: on_resume_click(converter, input_label, output_label, terminal, 
                                                               progress, resolution_choice, width_entry, 
                                                               height_entry, progress_text, stop_button, root))
    resume_button.grid(row=0, column=1, padx=5)
    resume_button.grid_remove()
    stop_button.grid_remove()  
    


    

    # Load last selected directories
    if input_dir and output_dir:
        input_label.config(text=input_dir)
        output_label.config(text=output_dir)
        update_image_count_label(input_dir, image_count_label)
        print_to_terminal(terminal, f"Input Directory: {input_dir}")
        print_to_terminal(terminal, f"Output Directory: {output_dir}")
    else:
        print_to_terminal(terminal, "Input Directory: Not selected")
        print_to_terminal(terminal, "Output Directory: Not selected")

    resolution_choice.trace_add('write', lambda *args: update_entry_visibility(resolution_choice, dimension_frame))

    doc_icon = ImageTk.PhotoImage(Image.open('icons/document_icon.png'))
    help_menu.entryconfig('Documentation', image=doc_icon, compound=tk.LEFT)

    input_label.grid_remove()
    output_label.grid_remove()
    root.mainloop()


def open_documentation():
    # open for future documentation
    pass

if __name__ == '__main__':
    try:
        initialize_gui()
    except Exception as e:
        print(f"Exception: {e}")
        logging.exception(f"Exception: {e}")

