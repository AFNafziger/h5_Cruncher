#!/usr/bin/env python3
"""
h5_cruncher2 - Main application entry point
Author: Atticus Nafziger with contributions from Claude and ChatGPT
"""
from ttkbootstrap import Window 
import tkinter as tk
from tkinter import messagebox
import traceback
import sys
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window import MainWindow


def main():
    """Main entry point for the application"""
    try:
        root = tk.Tk()
        app = MainWindow(root)
        app.run()
        
    except ImportError as e:
        messagebox.showerror("Import Error", 
                           f"Failed to import required modules: {str(e)}\n\n"
                           "Please ensure all required packages are installed:\n"
                           "pip install h5py numpy")
    except Exception as e:
        messagebox.showerror("Application Error", 
                           f"An unexpected error occurred: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    root = Window(themename="sandstone")
    app = MainWindow(root)
    app.run()