# Image Conversion and Resizing Script

This Python script converts `.jpg` images to `.webp` format and resizes them to 1440x1920 pixels. It also includes error handling and logs any errors to a file named `errors.log`. A progress bar and processing status are displayed in the terminal as images are processed.

## Dependencies

- Pillow
- tqdm
- tkinter

## Usage

Follow these steps to use the script:

1. **Install Required Library:**
    Before running the script, ensure you have Pillow installed:
    ```bash
    pip install Pillow
    ```
    
2. **Install tqdm Library:**
    This script also requires the tqdm library to display a progress bar:
    ```bash
    pip install tqdm
    ```

3. **Run the script:**
    ```bash
    python script.py
    ```

4. **Select Directories:**
   When you run the script, a dialog will pop up asking you to select the input directory (where your .jpg files are located) and then the output directory (where you want the .webp files to be saved).

5. **Check the Log:**
   If there are any errors during the process, they will be logged to `errors.log` in the directory from which you ran the script.

6. **Output:**
   The script will process each .jpg image in the input directory, convert it to .webp, resize it to 1440x1920, and save it in the output directory. It will not process images in subdirectories of the input directory.

Note: This script only processes .jpg files and does not process images in subdirectories.

## Features

- Converts .jpg images to .webp format.
- Resizes images to 1440x1920 pixels.
- Provides a progress bar to track the process.
- Logs errors to an `errors.log` file.

