"""
Dataset Inspector UI Module - Redesigned
Handles the dataset inspection window with column search and pagination
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from typing import Optional, List, Any, Dict
import pandas as pd
import numpy as np

from core.h5_file_handler import H5FileHandler
from core.data_formatter import DataFormatter


class DatasetInspector:
    """Handles dataset inspection window with column search and pagination"""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.inspector_window: Optional[tk.Toplevel] = None
        self.file_handler = H5FileHandler()
        self.formatter = DataFormatter()
        
        # Data management
        self.current_file_path: Optional[str] = None
        self.current_dataset_path: Optional[str] = None
        self.all_columns: List[str] = []
        self.filtered_columns: List[str] = []
        self.column_data_cache: Dict[str, List[Any]] = {}
        
        # Pagination
        self.columns_per_page = 100
        self.current_page = 0
        self.total_pages = 0
        
        # UI elements
        self.search_var: Optional[tk.StringVar] = None
        self.page_label: Optional[ttkb.Label] = None
        self.columns_frame: Optional[ttkb.Frame] = None
        self.canvas: Optional[tk.Canvas] = None
        self.scrollable_frame: Optional[ttkb.Frame] = None
    
    def inspect_dataset(self, file_path: str, dataset_path: str) -> None:
        """
        Open a new window to inspect the selected dataset with column exploration
        
        Args:
            file_path: Path to the HDF5 file
            dataset_path: Path to the dataset within the file
        """
        try:
            self.current_file_path = file_path
            self.current_dataset_path = dataset_path
            
            # Get dataset information
            info = self.file_handler.get_dataset_info(file_path, dataset_path)
            
            # Get column information
            self.all_columns = info.get('columns', [])
            
            if not self.all_columns:
                messagebox.showerror("Error", 
                    "This dataset doesn't appear to have identifiable columns. "
                    "Column exploration is only available for tabular datasets.")
                return
            
            # Initialize filtered columns and pagination
            self.filtered_columns = self.all_columns.copy()
            self._calculate_pagination()
            
            # Load first few rows of data for preview
            self._load_column_previews()
            
            # Create inspector window
            self._create_inspector_window(info)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to inspect dataset: {str(e)}")
    
    def _load_column_previews(self) -> None:
        """Load the first 3 rows of data for column previews"""
        try:
            self.column_data_cache.clear()
            
            # Read first 3 rows of the dataset
            sample_data = self.file_handler.read_dataset(
                self.current_file_path, 
                self.current_dataset_path, 
                slice_rows=(0, 3)  # First 3 rows
            )
            
            if isinstance(sample_data, pd.DataFrame):
                # For pandas DataFrame
                for col in self.all_columns:
                    if col in sample_data.columns:
                        self.column_data_cache[col] = sample_data[col].tolist()
                    else:
                        self.column_data_cache[col] = ["N/A", "N/A", "N/A"]
            else:
                # For numpy array or other data types
                if hasattr(sample_data, 'dtype') and sample_data.dtype.fields:
                    # Structured array
                    for col in self.all_columns:
                        if col in sample_data.dtype.names:
                            self.column_data_cache[col] = sample_data[col][:3].tolist()
                        else:
                            self.column_data_cache[col] = ["N/A", "N/A", "N/A"]
                else:
                    # Regular array - create generic column names
                    for i, col in enumerate(self.all_columns):
                        if i < sample_data.shape[1] if len(sample_data.shape) > 1 else 1:
                            if len(sample_data.shape) > 1:
                                self.column_data_cache[col] = sample_data[:3, i].tolist()
                            else:
                                self.column_data_cache[col] = sample_data[:3].tolist()
                        else:
                            self.column_data_cache[col] = ["N/A", "N/A", "N/A"]
            
            # Ensure all columns have exactly 3 preview values
            for col in self.all_columns:
                if col not in self.column_data_cache:
                    self.column_data_cache[col] = ["N/A", "N/A", "N/A"]
                else:
                    # Pad with N/A if less than 3 values
                    while len(self.column_data_cache[col]) < 3:
                        self.column_data_cache[col].append("N/A")
                    # Truncate if more than 3 values
                    self.column_data_cache[col] = self.column_data_cache[col][:3]
                        
        except Exception as e:
            print(f"Warning: Could not load column previews: {str(e)}")
            # Fallback: create empty previews
            for col in self.all_columns:
                self.column_data_cache[col] = ["N/A", "N/A", "N/A"]
    
    def _calculate_pagination(self) -> None:
        """Calculate pagination based on filtered columns"""
        self.total_pages = max(1, (len(self.filtered_columns) - 1) // self.columns_per_page + 1)
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
    
    def _create_inspector_window(self, info: dict) -> None:
        """
        Create and display the redesigned dataset inspector window
        
        Args:
            info: Dataset information dictionary
        """
        # Close existing inspector window if open
        if self.inspector_window:
            self.inspector_window.destroy()
        
        # Create new window
        self.inspector_window = ttkb.Toplevel(self.parent)
        self.inspector_window.title(f"Dataset Inspector - {info['path']}")
        self.inspector_window.geometry("780x550")
        self.inspector_window.resizable(True, True)
        
        # Configure grid
        self.inspector_window.grid_rowconfigure(0, weight=1)
        self.inspector_window.grid_columnconfigure(0, weight=1)
        
        # Create main container
        main_container = ttkb.Frame(self.inspector_window, padding=15)
        main_container.grid(row=0, column=0, sticky=NSEW)
        main_container.grid_rowconfigure(2, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create header
        self._create_header(main_container, info)
        
        # Create search bar
        self._create_search_bar(main_container)
        
        # Create column display area
        self._create_column_display(main_container)
        
        # Create pagination controls
        self._create_pagination_controls(main_container)
        
        # Center window
        self._center_window()
        
        # Initial column display
        self._update_column_display()
    
    def _create_header(self, parent: ttkb.Frame, info: dict) -> None:
        """Create the header with dataset information"""
        header_frame = ttkb.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(W, E), pady=(0, 15))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ttkb.Label(header_frame, text="Column Explorer", 
                               font=("Segoe UI", 16, "bold"), bootstyle="primary")
        title_label.grid(row=0, column=0, sticky=W)
        
        # Dataset info
        info_text = f"Dataset: {info['path']} | Shape: {info['shape']} | Columns: {len(self.all_columns)}"
        info_label = ttkb.Label(header_frame, text=info_text, 
                              font=("Segoe UI", 10), bootstyle="secondary")
        info_label.grid(row=1, column=0, sticky=W, pady=(5, 0))
    
    def _create_search_bar(self, parent: ttkb.Frame) -> None:
        """Create the search bar for filtering columns"""
        search_frame = ttkb.Frame(parent)
        search_frame.grid(row=1, column=0, sticky=(W, E), pady=(0, 15))
        search_frame.grid_columnconfigure(1, weight=1)
        
        # Search label
        search_label = ttkb.Label(search_frame, text="Search columns:", 
                                font=("Segoe UI", 11))
        search_label.grid(row=0, column=0, padx=(0, 10), sticky=W)
        
        # Search entry
        self.search_var = tk.StringVar()
        search_entry = ttkb.Entry(search_frame, textvariable=self.search_var, 
                                font=("Segoe UI", 10), bootstyle="info")
        search_entry.grid(row=0, column=1, sticky=(W, E), padx=(0, 10))
        
        # Bind search event
        self.search_var.trace('w', self._on_search_changed)
        
        # Clear search button
        clear_btn = ttkb.Button(search_frame, text="✕ Clear", 
                              command=self._clear_search, bootstyle="secondary-outline")
        clear_btn.grid(row=0, column=2)
        
        # Results info
        self.results_label = ttkb.Label(search_frame, text="", 
                                      font=("Segoe UI", 9), bootstyle="info")
        self.results_label.grid(row=1, column=0, columnspan=3, sticky=W, pady=(5, 0))
        
        # Update results info
        self._update_results_info()
    
    def _create_column_display(self, parent: ttkb.Frame) -> None:
        """Create the scrollable column display area"""
        display_frame = ttkb.LabelFrame(parent, text="Column Preview: first three rows of data", padding=10)
        display_frame.grid(row=2, column=0, sticky=NSEW)
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(display_frame, highlightthickness=0)
        scrollbar = ttkb.Scrollbar(display_frame, orient="vertical", 
                                 command=self.canvas.yview)
        self.scrollable_frame = ttkb.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid canvas and scrollbar
        self.canvas.grid(row=0, column=0, sticky=NSEW)
        scrollbar.grid(row=0, column=1, sticky=(N, S))
        
        # Configure scrollable frame
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mouse wheel
        self._bind_mouse_wheel()
    
    def _create_pagination_controls(self, parent: ttkb.Frame) -> None:
        """Create pagination controls"""
        pagination_frame = ttkb.Frame(parent)
        pagination_frame.grid(row=3, column=0, sticky=(W, E), pady=(15, 0))
        pagination_frame.grid_columnconfigure(2, weight=1)
        
        # Previous button
        prev_btn = ttkb.Button(pagination_frame, text="← Previous", 
                             command=self._previous_page, bootstyle="primary")
        prev_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Next button
        next_btn = ttkb.Button(pagination_frame, text="Next →", 
                             command=self._next_page, bootstyle="primary")
        next_btn.grid(row=0, column=1, padx=(0, 20))
        
        # Page info
        self.page_label = ttkb.Label(pagination_frame, text="", 
                                   font=("Segoe UI", 10))
        self.page_label.grid(row=0, column=2, sticky=W)
        
        # Close button
        close_btn = ttkb.Button(pagination_frame, text="Close", 
                              command=self.inspector_window.destroy, 
                              bootstyle="danger")
        close_btn.grid(row=0, column=3, sticky=E)
        
        # Update page info
        self._update_page_info()
    
    def _bind_mouse_wheel(self) -> None:
        """Bind mouse wheel scrolling to canvas"""
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Different binding for different platforms
        self.canvas.bind("<MouseWheel>", on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))   # Linux
        
        # Enable scrolling when mouse is over the canvas
        def bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", on_mousewheel)
            self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
            self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        
        def unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        
        self.canvas.bind('<Enter>', bind_to_mousewheel)
        self.canvas.bind('<Leave>', unbind_from_mousewheel)
    
    def _on_search_changed(self, *args) -> None:
        """Handle search text changes"""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            self.filtered_columns = self.all_columns.copy()
        else:
            self.filtered_columns = [
                col for col in self.all_columns
                if search_text in col.lower()
            ]
        
        # Reset pagination
        self.current_page = 0
        self._calculate_pagination()
        self._update_results_info()
        self._update_page_info()
        self._update_column_display()
    
    def _clear_search(self) -> None:
        """Clear the search field"""
        self.search_var.set("")
    
    def _update_results_info(self) -> None:
        """Update the results information label"""
        total_cols = len(self.all_columns)
        filtered_cols = len(self.filtered_columns)
        
        if filtered_cols == total_cols:
            text = f"Showing all {total_cols} columns"
        else:
            text = f"Showing {filtered_cols} of {total_cols} columns"
        
        self.results_label.config(text=text)
    
    def _previous_page(self) -> None:
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page_info()
            self._update_column_display()
    
    def _next_page(self) -> None:
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._update_page_info()
            self._update_column_display()
    
    def _update_page_info(self) -> None:
        """Update the page information label"""
        if self.total_pages <= 1:
            self.page_label.config(text="")
        else:
            self.page_label.config(text=f"Page {self.current_page + 1} of {self.total_pages}")
    
    def _update_column_display(self) -> None:
        """Update the column display with current page data"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Calculate column range for current page
        start_idx = self.current_page * self.columns_per_page
        end_idx = min(start_idx + self.columns_per_page, len(self.filtered_columns))
        page_columns = self.filtered_columns[start_idx:end_idx]
        
        if not page_columns:
            # No columns to display
            no_results_label = ttkb.Label(self.scrollable_frame, 
                                        text="No columns match your search criteria",
                                        font=("Segoe UI", 12, "italic"), 
                                        bootstyle="secondary")
            no_results_label.grid(row=0, column=0, pady=50)
            return
        
        # Create column widgets
        for i, column_name in enumerate(page_columns):
            column_index = self.all_columns.index(column_name) if column_name in self.all_columns else -1
            self._create_column_widget(i, column_index, column_name)
        
        # Update canvas scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0)  # Scroll to top
    
    def _create_column_widget(self, row: int, column_index: int, column_name: str) -> None:
        """Create a compact widget displaying column name, preview data, and type"""
        # Main column frame
        col_frame = ttkb.Frame(self.scrollable_frame, padding=5)
        col_frame.grid(row=row, column=0, sticky=(W, E), padx=2, pady=0)
        col_frame.grid_columnconfigure(0, weight=0)
        col_frame.grid_columnconfigure(1, weight=1)

        # Get preview data
        preview_data = self.column_data_cache.get(column_name, ["N/A", "N/A", "N/A"])
        formatted_values = [self._format_preview_value(v) for v in preview_data]
        preview_text = ", ".join(formatted_values)

        # First row: column name (bold/primary) + preview values (not bold/secondary)
        name_label = ttkb.Label(
            col_frame,
            text=f"{column_index}. {column_name}:",
            font=("Segoe UI", 10, "bold"),
            bootstyle="primary"
        )
        name_label.grid(row=0, column=0, sticky=W)

        preview_label = ttkb.Label(
            col_frame,
            text=f" {preview_text}",
            font=("Segoe UI", 8),  # Not bold
            bootstyle="success"
        )
        preview_label.grid(row=0, column=1, sticky=W)

        # Second row: data type
        try:
            sample = preview_data[0]
            if isinstance(sample, str):
                dtype_info = "string"
            elif isinstance(sample, (int, np.integer)):
                dtype_info = "integer"
            elif isinstance(sample, (float, np.floating)):
                dtype_info = "float"
            else:
                dtype_info = type(sample).__name__
        except:
            dtype_info = "unknown"

        type_label = ttkb.Label(
            col_frame,
            text=f"Type: {dtype_info}",
            font=("Segoe UI", 8, "italic"),
            bootstyle="secondary"
        )
        type_label.grid(row=1, column=0, columnspan=2, sticky=W, pady=(2, 0))

    
    def _format_preview_value(self, value: Any) -> str:
        """Format a preview value for display"""
        if value is None or pd.isna(value):
            return "N/A"
        
        # Convert value to string
        str_value = str(value)
        
        # Truncate long strings
        max_length = 60
        if len(str_value) > max_length:
            return str_value[:max_length] + "..."
        
        return str_value
    
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