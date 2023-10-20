# Image Conversion and Resizing Script

This Python script allows users to convert images from `.jpg` to `.webp` format and resize them either to recommended dimensions or to custom dimensions specified by the user. The script provides a user-friendly GUI for selecting input and output directories, specifying resolution preferences, and initiating the conversion process. Progress bars and a terminal are integrated within the GUI to provide real-time feedback on the conversion process. Additionally, the script handles errors gracefully, logging any exceptions to a file named `errors.log` for further investigation.

## Dependencies

- Python (3.6 or higher)
- Pillow (for image processing tasks)
- tkinter (to create the GUI)
- ttkthemes (to theme the tkinter GUI)
- ScrolledText (for the terminal widget within the GUI)

## Installation

1. Ensure you have Python 3.6 or higher installed on your machine.
2. Clone the repository or download the script to your local machine.
3. Install the required libraries using pip:

```bash
pip install Pillow ttkthemes
```

You can also install the dependencies from the `requirements.txt` file provided:

```bash
pip install -r requirements.txt
```

## Features

- User-friendly GUI for easy operation.
- Option to select recommended or custom image dimensions.
- Real-time feedback through progress bars and a terminal.
- Error handling with logging to a file for troubleshooting.
- Icons and a polished theme for a professional look and feel.

## Usage

1. Launch the script.
2. Select input and output directories using the provided buttons.
3. Choose either recommended dimensions or specify custom dimensions for resizing.
4. Click the "Convert" button to start the conversion process.
5. Monitor the progress on the progress bars and in the terminal.

The script is designed to be intuitive and user-friendly, making image conversion and resizing a breeze.
