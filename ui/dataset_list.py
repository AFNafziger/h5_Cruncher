"""
Dataset List UI Module
Handles the scrollable list of datasets
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from core.h5_file_handler import H5FileHandler


class DatasetList:
    """Handles the scrollable dataset list UI"""
    
    def __init__(self, parent: ttk.Frame, callback: Callable[[str], None]):
        self.parent = parent
        self.callback = callback
        self.datasets: List[str] = []
        self.current_file_path: Optional[str] = None
        
        # Add file handler for checking exportable datasets
        self.file_handler = H5FileHandler()
        
        # UI elements
        self.list_frame: Optional[ttk.LabelFrame] = None
        self.no_file_label: Optional[ttk.Label] = None
        self.scroll_container: Optional[ttk.Frame] = None
        self.canvas: Optional[tk.Canvas] = None
        self.scrollbar: Optional[ttk.Scrollbar] = None
        self.scrollable_frame: Optional[ttk.Frame] = None
        self.dataset_buttons: List[ttk.Button] = []
        self.search_var: Optional[tk.StringVar] = None
        self.search_entry: Optional[ttk.Entry] = None
        self.filtered_datasets: List[str] = []
    
    def create_ui(self, row: int) -> None:
        """
        Create the dataset list UI
        
        Args:
            row: Grid row to place the UI
        """
        # Create main frame
        self.list_frame = ttk.LabelFrame(self.parent, text="Available Datasets", 
                                        padding="15")
        self.list_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.list_frame.grid_rowconfigure(2, weight=1)
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        # Search bar (initially hidden)
        self._create_search_bar()
        
        # Initially show "no file loaded" message
        self._show_no_file_message()
    
    def _create_search_bar(self) -> None:
        """Create the search bar for filtering datasets"""
        search_frame = ttk.Frame(self.list_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)
        
        # Search label
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.grid(row=0, column=0, padx=(0, 8))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, 
                                     font=("TkDefaultFont", 9))
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 8))
        
        # Bind search event
        self.search_var.trace('w', self._on_search_changed)
        
        # Clear search button
        clear_search_btn = ttk.Button(search_frame, text="✕", width=3,
                                    command=self._clear_search)
        clear_search_btn.grid(row=0, column=2)
        
        # Initially hide search bar
        search_frame.grid_remove()
        self.search_frame = search_frame
    
    def _show_no_file_message(self) -> None:
        """Show the 'no file loaded' message"""
        self.no_file_label = ttk.Label(self.list_frame, 
                                      text="Load an H5 file to view datasets",
                                      font=("TkDefaultFont", 11, "italic"),
                                      foreground="gray")
        self.no_file_label.grid(row=1, column=0, pady=50)
    
    def _hide_no_file_message(self) -> None:
        """Hide the 'no file loaded' message"""
        if self.no_file_label:
            self.no_file_label.grid_remove()
    
    def _create_scrollable_list(self) -> None:
        """Create the scrollable dataset list"""
        # Remove existing scroll container if present
        if self.scroll_container:
            self.scroll_container.destroy()
        
        # Create scroll container
        self.scroll_container = ttk.Frame(self.list_frame)
        self.scroll_container.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scroll_container.grid_rowconfigure(0, weight=1)
        self.scroll_container.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.scroll_container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.scroll_container, orient="vertical", 
                                     command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid canvas and scrollbar
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure scrollable frame
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mouse wheel to canvas
        self._bind_mouse_wheel()
    
    def _bind_mouse_wheel(self) -> None:
        """Bind mouse wheel scrolling to canvas"""
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def on_mousewheel_linux(event):
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        
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
    
    def _is_exportable_dataframe(self, dataset_path: str) -> bool:
        """
        Check if a dataset is exportable as a DataFrame
        
        Args:
            dataset_path: Path to the dataset
            
        Returns:
            True if the dataset can be exported as a DataFrame, False otherwise
        """
        if not self.current_file_path:
            return False
            
        try:
            # Get dataset information
            info = self.file_handler.get_dataset_info(self.current_file_path, dataset_path)
            
            # Check if it has identifiable columns
            has_columns = 'columns' in info and info['columns'] and len(info['columns']) > 0
            
            # Check if it has a valid tabular shape
            has_valid_shape = False
            if 'shape' in info:
                if isinstance(info['shape'], tuple) and len(info['shape']) >= 1:
                    # Must have at least some rows
                    if isinstance(info['shape'][0], int) and info['shape'][0] > 0:
                        has_valid_shape = True
                elif info['shape'] == 'Inferred':  # For pandas HDFStore groups
                    has_valid_shape = True
            
            # Dataset is exportable if it has both columns and valid shape
            is_exportable = has_columns and has_valid_shape
                
            return is_exportable
            
        except Exception as e:
            print(f"Error checking exportability for {dataset_path}: {str(e)}")
            return False
    
    def _create_dataset_buttons(self, datasets: List[str]) -> None:
        """
        Create buttons for the dataset list with styling based on exportability
        
        Args:
            datasets: List of dataset paths to create buttons for
        """
        # Clear existing buttons
        for button in self.dataset_buttons:
            button.destroy()
        self.dataset_buttons.clear()
        
        # Create new buttons
        exportable_count = 0
        for i, dataset_path in enumerate(datasets):
            # Check if dataset is exportable
            is_exportable = self._is_exportable_dataframe(dataset_path)
            if is_exportable:
                exportable_count += 1
            
            # Choose button style based on exportability
            if is_exportable:
                # Use ttkbootstrap button with success style for exportable datasets
                btn = ttkb.Button(
                    self.scrollable_frame,
                    text=f"{self._format_dataset_name(dataset_path)}",
                    command=lambda path=dataset_path: self.callback(path),
                    bootstyle="success",
                    width=70
                )
            else:
                # Use regular ttk button for non-exportable datasets
                btn = ttk.Button(
                    self.scrollable_frame,
                    text=f"{self._format_dataset_name(dataset_path)}",
                    command=lambda path=dataset_path: self.callback(path),
                    width=70
                )
            
            btn.grid(row=i, column=0, sticky=(tk.W, tk.E), padx=5, pady=3)
            
            # Add hover effect
            self._add_hover_effect(btn)
            
            # Store button reference
            self.dataset_buttons.append(btn)
        
        # Add summary label
        if datasets:
            summary_text = f"Total: {len(datasets)} dataset{'s' if len(datasets) != 1 else ''}"
            if exportable_count > 0:
                summary_text += f" ({exportable_count} exportable)"
                
            count_label = ttk.Label(self.scrollable_frame, 
                                  text=summary_text,
                                  font=("TkDefaultFont", 8), foreground="gray")
            count_label.grid(row=len(datasets), column=0, pady=(15, 5))
            self.dataset_buttons.append(count_label)  # Store for cleanup
    
    def _format_dataset_name(self, dataset_path: str) -> str:
        """
        Format dataset name for display
        
        Args:
            dataset_path: Original dataset path
            
        Returns:
            Formatted display name
        """
        # If path is too long, show abbreviated version
        if len(dataset_path) > 60:
            parts = dataset_path.split('/')
            if len(parts) > 2:
                return f"{parts[0]}/.../{parts[-1]}"
        
        return dataset_path
    
    def _add_hover_effect(self, button) -> None:
        """Add hover effect to button"""
        def on_enter(e):
            button.configure(cursor="hand2")
        
        def on_leave(e):
            button.configure(cursor="")
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def _on_search_changed(self, *args) -> None:
        """Handle search text changes"""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            # Show all datasets
            self.filtered_datasets = self.datasets.copy()
        else:
            # Filter datasets
            self.filtered_datasets = [
                dataset for dataset in self.datasets
                if search_text in dataset.lower()
            ]
        
        # Update button list
        self._create_dataset_buttons(self.filtered_datasets)
    
    def _clear_search(self) -> None:
        """Clear the search field"""
        self.search_var.set("")
    
    def update_datasets(self, datasets: List[str], file_path: str = None) -> None:
        """
        Update the dataset list
        
        Args:
            datasets: New list of datasets
            file_path: Path to the current file (for exportability checking)
        """
        self.datasets = datasets
        self.filtered_datasets = datasets.copy()
        self.current_file_path = file_path  # Store file path for exportability checking
        
        # Hide no file message
        self._hide_no_file_message()
        
        # Show search bar if we have datasets
        if datasets:
            self.search_frame.grid()
            self._clear_search()  # Clear any existing search
        
        # Create scrollable list
        self._create_scrollable_list()
        
        # Create dataset buttons with exportability styling
        self._create_dataset_buttons(datasets)
    
    def clear_datasets(self) -> None:
        """Clear all datasets and show no file message"""
        self.datasets.clear()
        self.filtered_datasets.clear()
        self.current_file_path = None
        
        # Hide search bar
        if hasattr(self, 'search_frame'):
            self.search_frame.grid_remove()
        
        # Remove scroll container
        if self.scroll_container:
            self.scroll_container.destroy()
            self.scroll_container = None
        
        # Show no file message
        self._show_no_file_message()
    
    def get_selected_datasets(self) -> List[str]:
        """Get the currently displayed (filtered) datasets"""
        return self.filtered_datasets.copy()