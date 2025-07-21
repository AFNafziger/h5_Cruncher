# ui/specific_instance_export_window.py
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, END, W, E, NSEW, BOTH, LEFT, RIGHT, Y
import pandas as pd
import math
from typing import List, Optional, Any

from core.h5_file_handler import H5FileHandler
from core.dataframe_exporter import DataFrameExporter


class SpecificInstanceExportWindow:
    def __init__(self, master: ttkb.Window, h5_file_path: str, dataset_path: str):
        self.master = master
        self.h5_file_path = h5_file_path
        self.dataset_path = dataset_path
        self.file_handler = H5FileHandler()
        self.dataframe_exporter = DataFrameExporter()

        # Core data variables
        self.df_columns: List[str] = []
        self.selected_column: Optional[str] = None
        self.search_value: str = ""
        self.filtered_df: Optional[pd.DataFrame] = None
        self.preview_rows: int = 0
        self.preview_columns: int = 0

        # Pagination variables (borrowed from export window)
        self.columns_per_page: int = 20
        self.current_page: int = 0
        self.filtered_columns: List[str] = []
        self.total_pages: int = 0
        
        # Column management (keeping structure consistent with export window)
        self.column_checkboxes = {}  # Not used but keeping for consistency
        self.column_vars = {}        # Not used but keeping for consistency

        self.dialog = ttkb.Toplevel(master)
        self.dialog.title(f"Specific Instance Export: {dataset_path.split('/')[-1]}")
        self.dialog.geometry("800x600")
        self.dialog.transient(master)
        self.dialog.grab_set()

        self._center_dialog()
        self._setup_ui()
        self._load_columns()

    def _center_dialog(self) -> None:
        """Center the dialog on the screen"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        main_frame = ttkb.Frame(self.dialog, padding=15)
        main_frame.pack(fill=BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left Panel: Column Selection (borrowed structure from export window)
        left_frame = ttkb.Frame(main_frame, relief="solid", borderwidth=1, padding=10)
        left_frame.grid(row=0, column=0, sticky=NSEW, padx=(0, 10))
        left_frame.grid_rowconfigure(2, weight=1)  # Make column list expandable
        left_frame.grid_columnconfigure(0, weight=1)

        ttkb.Label(left_frame, text="Select Column:", bootstyle="primary").grid(row=0, column=0, sticky=W, pady=(0, 10))

        # Search frame
        search_frame = ttkb.Frame(left_frame)
        search_frame.grid(row=1, column=0, sticky=EW, pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)

        self.column_search_var = ttkb.StringVar()
        search_entry = ttkb.Entry(search_frame, textvariable=self.column_search_var, bootstyle="info")
        search_entry.grid(row=0, column=1, sticky=EW, padx=(0, 8))
        
        # Insert placeholder text first
        search_entry.insert(0, "Search columns...")
        search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, END) if search_entry.get() == "Search columns..." else None)

        clear_search_btn = ttkb.Button(search_frame, text="✕", width=3, command=self._clear_search, bootstyle="secondary-outline")
        clear_search_btn.grid(row=0, column=2)

        # Column list frame (scrollable)
        self.column_list_frame = ttkb.Frame(left_frame)
        self.column_list_frame.grid(row=2, column=0, sticky=NSEW)
        self.column_list_frame.grid_columnconfigure(0, weight=1)
        self.column_list_frame.grid_rowconfigure(0, weight=1)

        # Pagination and action buttons frame
        pagination_frame = ttkb.Frame(left_frame)
        pagination_frame.grid(row=3, column=0, sticky=EW, pady=(10, 0))
        pagination_frame.grid_columnconfigure(1, weight=1)

        # Pagination controls
        nav_frame = ttkb.Frame(pagination_frame)
        nav_frame.grid(row=0, column=0, sticky=W)

        self.prev_btn = ttkb.Button(nav_frame, text="◀ Previous", command=self._previous_page,
                                    bootstyle="secondary-outline", state=DISABLED)
        self.prev_btn.pack(side=LEFT, padx=(0, 5))

        self.page_label = ttkb.Label(nav_frame, text="Page 1 of 1")
        self.page_label.pack(side=LEFT, padx=10)

        self.next_btn = ttkb.Button(nav_frame, text="Next ▶", command=self._next_page,
                                    bootstyle="secondary-outline", state=DISABLED)
        self.next_btn.pack(side=LEFT, padx=(5, 0))

        # Action buttons - adapted for single selection
        action_frame = ttkb.Frame(pagination_frame)
        action_frame.grid(row=1, column=0, columnspan=2, sticky=EW, pady=(10, 0))

        clear_selection_button = ttkb.Button(action_frame, text="Clear Selection",
                                           command=self._clear_selection, bootstyle="warning-outline")
        clear_selection_button.pack(side=LEFT, padx=(0, 5))

        # Right Panel: Value Input and Preview
        right_frame = ttkb.Frame(main_frame, relief="solid", borderwidth=1, padding=10)
        right_frame.grid(row=0, column=1, sticky=NSEW, padx=(10, 0))
        right_frame.grid_rowconfigure(4, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Value input
        ttkb.Label(right_frame, text="Enter value to match:", bootstyle="primary").grid(row=0, column=0, sticky=W, pady=(0, 10))
        
        self.value_var = ttkb.StringVar()
        self.value_var.trace_add("write", self._on_value_changed)
        self.value_entry = ttkb.Entry(right_frame, textvariable=self.value_var, bootstyle="info")
        self.value_entry.grid(row=1, column=0, sticky=EW, pady=(0, 15))

        # Preview section
        ttkb.Label(right_frame, text="Preview:", bootstyle="primary").grid(row=2, column=0, sticky=W, pady=(0, 10))
        
        self.preview_label = ttkb.Label(
            right_frame, 
            text="Select column and enter value",
            bootstyle="secondary",
            wraplength=300
        )
        self.preview_label.grid(row=3, column=0, sticky=W, pady=(0, 10))

        # Sample data display
        sample_frame = ttkb.LabelFrame(right_frame, text="Sample Matching Rows", padding=5)
        sample_frame.grid(row=4, column=0, sticky=NSEW)
        sample_frame.grid_rowconfigure(0, weight=1)
        sample_frame.grid_columnconfigure(0, weight=1)

        self.sample_text = ttkb.ScrolledText(sample_frame, height=10, width=50)
        self.sample_text.pack(fill=BOTH, expand=True)
        self.sample_text.insert(END, "No preview available")
        self.sample_text.config(state="disabled")

        # Bottom Panel: Export Controls
        bottom_frame = ttkb.Frame(main_frame, padding=(0, 15))
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky=EW)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, weight=1)

        # Status/Info
        self.status_label = ttkb.Label(
            bottom_frame, 
            text="Ready - Select column and value to continue",
            bootstyle="info"
        )
        self.status_label.grid(row=0, column=0, sticky=W)

        # Buttons
        ttkb.Button(
            bottom_frame, 
            text="Preview", 
            bootstyle="secondary",
            command=self._update_preview
        ).grid(row=0, column=1, sticky=EW, padx=10)

        self.export_button = ttkb.Button(
            bottom_frame, 
            text="Export CSV", 
            bootstyle="success",
            command=self._export_csv,
            state="disabled"
        )
        self.export_button.grid(row=0, column=2, sticky=E)

    # ALL BORROWED METHODS FROM EXPORT WINDOW (properly adapted)
    
    def _load_columns(self) -> None:
        """Load columns from the dataset (borrowed from export window)"""
        try:
            # Use the updated get_dataset_info which now includes 'columns' for groups
            info = self.file_handler.get_dataset_info(self.h5_file_path, self.dataset_path)
            if 'columns' in info and info['columns']:
                self.df_columns = info['columns']
            else:
                self.df_columns = [] # No columns found or not a tabular dataset

            if not self.df_columns:
                Messagebox.show_warning(
                    f"No columns could be identified for dataset '{self.dataset_path.split('/')[-1]}'. "
                    "This might not be a tabular dataset or its structure is not recognized for column extraction.",
                    title="No Columns Identified"
                )
                self.dialog.destroy()
                return

            # Initialize filtered columns (no filter applied initially)
            self.filtered_columns = self.df_columns.copy()
            
            # Calculate pagination
            self._update_pagination()
            
            # Display first page
            self._populate_current_page()
            
            # Now that everything is set up, add the trace for search
            self.column_search_var.trace_add("write", self._filter_columns)
            
        except Exception as e:
            Messagebox.show_error(f"Failed to load dataset columns: {str(e)}", title="Error")
            self.dialog.destroy()

    def _update_pagination(self) -> None:
        """Update pagination information based on filtered columns (borrowed from export window)"""
        self.total_pages = max(1, math.ceil(len(self.filtered_columns) / self.columns_per_page))
        
        # Reset to first page if current page is out of bounds
        if self.current_page >= self.total_pages:
            self.current_page = 0
            
        self._update_pagination_controls()

    def _update_pagination_controls(self) -> None:
        """Update pagination control states and labels (borrowed from export window)"""
        # Only update if UI elements have been created
        if not hasattr(self, 'page_label') or not hasattr(self, 'prev_btn') or not hasattr(self, 'next_btn'):
            return
            
        # Update page label
        self.page_label.config(text=f"Page {self.current_page + 1} of {self.total_pages}")
        
        # Update button states
        self.prev_btn.config(state=NORMAL if self.current_page > 0 else DISABLED)
        self.next_btn.config(state=NORMAL if self.current_page < self.total_pages - 1 else DISABLED)

    def _previous_page(self) -> None:
        """Navigate to previous page (borrowed from export window)"""
        if self.current_page > 0:
            self.current_page -= 1
            self._populate_current_page()
            self._update_pagination_controls()

    def _next_page(self) -> None:
        """Navigate to next page (borrowed from export window)"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._populate_current_page()
            self._update_pagination_controls()

    def _get_current_page_columns(self) -> List[str]:
        """Get columns for the current page (borrowed from export window)"""
        start_idx = self.current_page * self.columns_per_page
        end_idx = start_idx + self.columns_per_page
        return self.filtered_columns[start_idx:end_idx]

    def _populate_current_page(self) -> None:
        """Populate the column list with current page columns (borrowed from export window, adapted for radio buttons)"""
        # Don't populate if UI isn't ready yet
        if not hasattr(self, 'column_list_frame') or not self.column_list_frame.winfo_exists():
            return
            
        # Clear existing widgets
        for widget in self.column_list_frame.winfo_children():
            widget.destroy()

        current_page_columns = self._get_current_page_columns()

        if not current_page_columns:
            # No columns to display
            no_cols_label = ttkb.Label(self.column_list_frame, text="No columns found", 
                                      bootstyle="secondary")
            no_cols_label.pack(pady=20)
            return

        # Create a scrollable frame for radio buttons
        canvas = ttkb.Canvas(self.column_list_frame, height=250)  # Set a fixed height
        scrollbar = ttkb.Scrollbar(self.column_list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttkb.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Create radio buttons for current page columns only - ADAPTED FOR SINGLE SELECTION
        if not hasattr(self, 'column_var'):
            self.column_var = ttkb.StringVar()
            self.column_var.trace_add("write", self._on_column_selected)

        for col in current_page_columns:
            rb = ttkb.Radiobutton(
                scrollable_frame, 
                text=col, 
                variable=self.column_var, 
                value=col,
                bootstyle="primary"
            )
            rb.pack(anchor=W, pady=3, padx=5)

        # Bind mouse wheel scrolling (borrowed from export window)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_linux)

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)
        scrollable_frame.bind("<Enter>", _bind_mousewheel)
        scrollable_frame.bind("<Leave>", _unbind_mousewheel)

    def _filter_columns(self, *args) -> None:
        """Filter columns based on search term (borrowed from export window)"""
        # Don't filter if columns haven't been loaded yet
        if not hasattr(self, 'df_columns') or not self.df_columns:
            return
            
        search_term = self.column_search_var.get().lower()
        
        if not search_term or search_term == "search columns...":
            # Show all columns
            self.filtered_columns = self.df_columns.copy()
        else:
            # Filter columns
            self.filtered_columns = [
                col for col in self.df_columns
                if search_term in col.lower()
            ]
        
        # Reset to first page and update
        self.current_page = 0
        self._update_pagination()
        
        # Only populate if UI is ready
        if hasattr(self, 'column_list_frame'):
            self._populate_current_page()

    def _clear_search(self) -> None:
        """Clear the search field (borrowed from export window)"""
        self.column_search_var.set("")

    def _clear_selection(self) -> None:
        """Clear the current column selection"""
        if hasattr(self, 'column_var'):
            self.column_var.set("")
        self.selected_column = None
        self._update_preview()

    # SPECIFIC INSTANCE METHODS (unique to this window)
    
    def _on_column_selected(self, *args) -> None:
        """Handle column selection"""
        self.selected_column = self.column_var.get()
        self._update_preview()

    def _on_value_changed(self, *args) -> None:
        """Handle value input change"""
        self.search_value = self.value_var.get()
        self._update_preview()

    def _update_preview(self) -> None:
        """Update the preview based on current selection"""
        if not self.selected_column or not self.search_value:
            self.preview_label.config(text="Select column and enter value", bootstyle="secondary")
            self.sample_text.config(state="normal")
            self.sample_text.delete(1.0, END)
            self.sample_text.insert(END, "No preview available")
            self.sample_text.config(state="disabled")
            self.export_button.config(state="disabled")
            self.status_label.config(text="Ready - Select column and value to continue", bootstyle="info")
            return

        try:
            # Load the dataset and filter it
            self.status_label.config(text="Loading data...", bootstyle="warning")
            self.dialog.update()

            # Read the dataset
            full_data = self.file_handler.read_dataset(self.h5_file_path, self.dataset_path)
            
            if not isinstance(full_data, pd.DataFrame):
                raise ValueError("Dataset is not in a compatible format for filtering")

            # Filter the data
            if self.selected_column not in full_data.columns:
                raise ValueError(f"Column '{self.selected_column}' not found in dataset")

            # Handle different data types for exact comparison
            column_data = full_data[self.selected_column]
            
            # Try exact matching based on data type
            if pd.api.types.is_numeric_dtype(column_data):
                try:
                    # For numeric columns, try to convert search value to number for exact match
                    search_value_converted = pd.to_numeric(self.search_value)
                    mask = column_data == search_value_converted
                except (ValueError, TypeError):
                    # If conversion fails, do exact string comparison
                    mask = column_data.astype(str) == str(self.search_value)
            else:
                # For non-numeric data, do exact string matching
                mask = column_data.astype(str) == str(self.search_value)

            self.filtered_df = full_data[mask].copy()
            
            self.preview_rows = len(self.filtered_df)
            self.preview_columns = len(self.filtered_df.columns)

            if self.preview_rows == 0:
                self.preview_label.config(
                    text=f"No rows found where '{self.selected_column}' matches '{self.search_value}'",
                    bootstyle="warning"
                )
                self.sample_text.config(state="normal")
                self.sample_text.delete(1.0, END)
                self.sample_text.insert(END, "No matching rows found")
                self.sample_text.config(state="disabled")
                self.export_button.config(state="disabled")
                self.status_label.config(text="No matches found", bootstyle="warning")
            else:
                self.preview_label.config(
                    text=f"Found {self.preview_rows:,} rows × {self.preview_columns} columns",
                    bootstyle="success"
                )
                
                # Show sample of the filtered data
                sample_size = min(5, self.preview_rows)
                sample_data = self.filtered_df.head(sample_size)
                
                self.sample_text.config(state="normal")
                self.sample_text.delete(1.0, END)
                self.sample_text.insert(END, f"First {sample_size} matching rows:\n")
                self.sample_text.insert(END, "=" * 50 + "\n")
                self.sample_text.insert(END, sample_data.to_string(max_cols=3, max_colwidth=15))
                if self.preview_rows > sample_size:
                    self.sample_text.insert(END, f"\n\n... and {self.preview_rows - sample_size} more rows")
                self.sample_text.config(state="disabled")
                
                self.export_button.config(state="normal")
                self.status_label.config(text=f"Ready to export {self.preview_rows:,} rows", bootstyle="success")

        except Exception as e:
            self.preview_label.config(text=f"Error: {str(e)}", bootstyle="danger")
            self.sample_text.config(state="normal")
            self.sample_text.delete(1.0, END)
            self.sample_text.insert(END, f"Error occurred: {str(e)}")
            self.sample_text.config(state="disabled")
            self.export_button.config(state="disabled")
            self.status_label.config(text="Error occurred", bootstyle="danger")

    def _export_csv(self) -> None:
        """Export the filtered data to CSV"""
        if self.filtered_df is None or len(self.filtered_df) == 0:
            Messagebox.show_warning("No data to export", title="Export Error")
            return

        # Confirm export
        confirm_text = (f"Export {self.preview_rows:,} rows × {self.preview_columns} columns "
                       f"where '{self.selected_column}' matches '{self.search_value}'?")
        if not Messagebox.okcancel(confirm_text, title="Confirm Export"):
            return

        # Ask for save location
        safe_value = "".join(c for c in self.search_value if c.isalnum() or c in (' ', '-', '_')).rstrip()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Filtered CSV As",
            initialvalue=f"{self.dataset_path.split('/')[-1]}_{self.selected_column}_{safe_value}.csv"
        )
        
        if not file_path:
            return  # User cancelled

        try:
            self.status_label.config(text="Exporting...", bootstyle="info")
            self.dialog.update()
            
            # Export the filtered dataframe directly
            self.filtered_df.to_csv(file_path, index=False)
            
            Messagebox.show_info(
                f"Successfully exported {self.preview_rows:,} rows to:\n{file_path}",
                title="Export Complete"
            )
        except Exception as e:
            Messagebox.show_error(f"Failed to export data: {str(e)}", title="Export Error")
        finally:
            self.dialog.destroy()