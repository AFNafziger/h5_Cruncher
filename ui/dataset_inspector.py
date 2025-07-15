"""
Dataset Inspector UI Module
Handles the dataset inspection window and data display
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional

from core.h5_file_handler import H5FileHandler
from core.data_formatter import DataFormatter


class DatasetInspector:
    """Handles dataset inspection window and data display"""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.inspector_window: Optional[tk.Toplevel] = None
        self.file_handler = H5FileHandler()
        self.formatter = DataFormatter()
    
    def inspect_dataset(self, file_path: str, dataset_path: str) -> None:
        """
        Open a new window to inspect the selected dataset
        
        Args:
            file_path: Path to the HDF5 file
            dataset_path: Path to the dataset within the file
        """
        try:
            # Get dataset information
            info = self.file_handler.get_dataset_info(file_path, dataset_path)
            
            # Get dataset data
            data, is_truncated = self.file_handler.get_dataset_data(file_path, dataset_path)
            
            # Format data for display
            formatted_data = self.formatter.format_for_display(
                data, is_truncated, info['shape']
            )
            
            # Create inspector window
            self._create_inspector_window(info, formatted_data, is_truncated)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to inspect dataset: {str(e)}")
    
    def _create_inspector_window(self, info: dict, formatted_data: str, is_truncated: bool) -> None:
        """
        Create and display the dataset inspector window
        
        Args:
            info: Dataset information dictionary
            formatted_data: Formatted data string for display
            is_truncated: Whether the data was truncated
        """
        # Close existing inspector window if open
        if self.inspector_window:
            self.inspector_window.destroy()
        
        # Create new window
        self.inspector_window = tk.Toplevel(self.parent)
        self.inspector_window.title(f"Dataset Inspector - {info['path']}")
        self.inspector_window.geometry("900x700")
        
        # Make window resizable
        self.inspector_window.resizable(True, True)
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self.inspector_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_info_tab(notebook, info)
        self._create_data_tab(notebook, formatted_data, is_truncated)
        
        # Set focus to data tab by default
        notebook.select(1)
        
        # Center window
        self._center_window()
    
    def _create_info_tab(self, notebook: ttk.Notebook, info: dict) -> None:
        """
        Create the dataset information tab
        
        Args:
            notebook: Parent notebook widget
            info: Dataset information dictionary
        """
        # Create info frame
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="Dataset Info")
        
        # Configure grid
        info_frame.grid_rowconfigure(0, weight=1)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Create main container
        main_container = ttk.Frame(info_frame, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_container.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_container, text="Dataset Information", 
                               font=("TkDefaultFont", 12, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 15))
        
        # Information display
        info_text = scrolledtext.ScrolledText(main_container, wrap=tk.WORD, 
                                            font=("Courier", 10), height=20)
        info_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Format and insert information
        formatted_info = self.formatter.format_dataset_info(info)
        info_text.insert(tk.END, formatted_info)
        info_text.config(state=tk.DISABLED)  # Make read-only
        
        # Configure grid weights
        main_container.grid_rowconfigure(1, weight=1)
    
    def _create_data_tab(self, notebook: ttk.Notebook, formatted_data: str, is_truncated: bool) -> None:
        """
        Create the dataset data tab
        
        Args:
            notebook: Parent notebook widget
            formatted_data: Formatted data string
            is_truncated: Whether the data was truncated
        """
        # Create data frame
        data_frame = ttk.Frame(notebook)
        notebook.add(data_frame, text="Dataset Contents")
        
        # Configure grid
        data_frame.grid_rowconfigure(1, weight=1)
        data_frame.grid_columnconfigure(0, weight=1)
        
        # Create main container
        main_container = ttk.Frame(data_frame, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        # Header with truncation warning if needed
        header_frame = ttk.Frame(main_container)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ttk.Label(header_frame, text="Dataset Contents", 
                               font=("TkDefaultFont", 12, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        if is_truncated:
            warning_label = ttk.Label(header_frame, 
                                    text="⚠️ Large dataset - showing limited preview", 
                                    foreground="orange",
                                    font=("TkDefaultFont", 9, "italic"))
            warning_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Data display area
        data_text = scrolledtext.ScrolledText(main_container, wrap=tk.NONE, 
                                            font=("Courier", 9))
        data_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Insert formatted data
        data_text.insert(tk.END, formatted_data)
        data_text.config(state=tk.DISABLED)  # Make read-only
        
        # Add horizontal scrollbar for wide content
        h_scrollbar = ttk.Scrollbar(main_container, orient=tk.HORIZONTAL, 
                                  command=data_text.xview)
        h_scrollbar.grid(row=2, column=0, sticky=(tk.W, tk.E))
        data_text.configure(xscrollcommand=h_scrollbar.set)
        
        # Close button
        close_button = ttk.Button(main_container, text="Close", 
                                command=self.inspector_window.destroy)
        close_button.grid(row=3, column=0, pady=(10, 0))
    
    def _center_window(self) -> None:
        """Center the inspector window on screen"""
        if not self.inspector_window:
            return
        
        self.inspector_window.update_idletasks()
        width = self.inspector_window.winfo_width()
        height = self.inspector_window.winfo_height()
        x = (self.inspector_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.inspector_window.winfo_screenheight() // 2) - (height // 2)
        self.inspector_window.geometry(f"{width}x{height}+{x}+{y}")
    
    def close_inspector(self) -> None:
        """Close the inspector window if it exists"""
        if self.inspector_window:
            self.inspector_window.destroy()
            self.inspector_window = None