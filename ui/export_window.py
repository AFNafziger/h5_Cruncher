# ui/export_window.py
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, END, W, E, NSEW, BOTH, LEFT, RIGHT, Y
import pandas as pd
from typing import List, Optional, Tuple, Any
import math

from core.h5_file_handler import H5FileHandler
from core.dataframe_exporter import DataFrameExporter


class ExportWindow:
    def __init__(self, master: ttkb.Window, h5_file_path: str, dataset_path: str):
        self.master = master
        self.h5_file_path = h5_file_path
        self.dataset_path = dataset_path
        self.file_handler = H5FileHandler()
        self.dataframe_exporter = DataFrameExporter()

        self.df_columns: List[str] = []
        self.selected_columns: List[str] = []
        self.row_selection_string: str = ""
        
        # Pagination variables
        self.columns_per_page = 250
        self.current_page = 0
        self.total_pages = 0
        self.filtered_columns: List[str] = []  # For search functionality
        
        # Column selection tracking (persists across pages)
        self.column_vars = {}  # BooleanVar for each column (across all pages)
        self.column_checkboxes = {}  # Only current page checkboxes

        self.dialog = ttkb.Toplevel(master)
        self.dialog.title(f"Export Dataset: {dataset_path.split('/')[-1]}")
        self.dialog.geometry("800x600")
        self.dialog.transient(master)
        self.dialog.grab_set()

        self._center_dialog()
        self._setup_ui()
        self._load_columns()

    def _center_dialog(self) -> None:
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _setup_ui(self) -> None:
        main_frame = ttkb.Frame(self.dialog, padding=15)
        main_frame.pack(fill=BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left Panel: Item Selector (Columns)
        left_frame = ttkb.Frame(main_frame, relief="solid", borderwidth=1, padding=10)
        left_frame.grid(row=0, column=0, sticky=NSEW, padx=(0, 10))
        left_frame.grid_rowconfigure(2, weight=1)  # Make column list expandable
        left_frame.grid_columnconfigure(0, weight=1)

        ttkb.Label(left_frame, text="Select Columns:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky=W, pady=(0, 10))

        # Search frame
        search_frame = ttkb.Frame(left_frame)
        search_frame.grid(row=1, column=0, sticky=EW, pady=(0, 10))
        search_frame.grid_columnconfigure(1, weight=1)

        self.column_search_var = ttkb.StringVar()
        search_entry = ttkb.Entry(search_frame, textvariable=self.column_search_var, bootstyle="info")
        search_entry.grid(row=0, column=1, sticky=EW, padx=(0, 8))
        
        # Insert placeholder text first, then bind events
        search_entry.insert(0, "Search columns...")
        
        # Bind events after inserting placeholder
        self.column_search_var.trace_add("write", self._filter_columns)
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

        self.page_label = ttkb.Label(nav_frame, text="Page 1 of 1", font=("Segoe UI", 9))
        self.page_label.pack(side=LEFT, padx=10)

        self.next_btn = ttkb.Button(nav_frame, text="Next ▶", command=self._next_page, 
                                   bootstyle="secondary-outline", state=DISABLED)
        self.next_btn.pack(side=LEFT, padx=(5, 0))

        # Action buttons
        action_frame = ttkb.Frame(pagination_frame)
        action_frame.grid(row=1, column=0, columnspan=2, sticky=EW, pady=(10, 0))

        select_all_button = ttkb.Button(action_frame, text="Select All (current page)", 
                                       command=self._select_all_current_page, bootstyle="info-outline")
        select_all_button.pack(side=LEFT, padx=(0, 5))

        select_all_filtered_button = ttkb.Button(action_frame, text="Select All (filtered)", 
                                               command=self._select_all_filtered_columns, bootstyle="info-outline")
        select_all_filtered_button.pack(side=LEFT, padx=5)

        deselect_all_button = ttkb.Button(action_frame, text="Deselect All", 
                                        command=self._deselect_all_columns, bootstyle="warning-outline")
        deselect_all_button.pack(side=LEFT, padx=5)

        # Right Panel: Value Selector (Rows)
        right_frame = ttkb.Frame(main_frame, relief="solid", borderwidth=1, padding=10)
        right_frame.grid(row=0, column=1, sticky=NSEW, padx=(10, 0))
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        ttkb.Label(right_frame, text="Select Rows (e.g., 1-100,200,500):", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky=W, pady=(0, 10))
        self.row_selection_entry = ttkb.Entry(right_frame, bootstyle="info")
        self.row_selection_entry.grid(row=1, column=0, sticky=EW, pady=(0, 10))
        self.row_selection_entry.insert(0, "Leave blank for all rows")
        self.row_selection_entry.bind("<FocusIn>", lambda e: self.row_selection_entry.delete(0, END) if self.row_selection_entry.get() == "Leave blank for all rows" else None)

        ttkb.Label(right_frame, text="Excel's row limit is approx. 1,048,576 rows.", font=("Segoe UI", 9), bootstyle="warning").grid(row=2, column=0, sticky=W, pady=(5, 0))

        export_max_rows_btn = ttkb.Button(right_frame, text="Export Max Excel Rows", command=self._export_max_excel_rows, bootstyle="info-outline")
        export_max_rows_btn.grid(row=3, column=0, sticky=EW, pady=(10, 0))

        # Bottom Panel: Export and Info
        bottom_frame = ttkb.Frame(main_frame, padding=(0, 10))
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky=EW)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, weight=1)

        self.preview_label = ttkb.Label(bottom_frame, text="Rows: 0 × Columns: 0", font=("Segoe UI", 10))
        self.preview_label.grid(row=0, column=0, sticky=W)

        ttkb.Button(bottom_frame, text="Preview (Do Before Export)", command=self._preview_export, bootstyle="info").grid(row=0, column=1, sticky=EW, padx=10)
        ttkb.Button(bottom_frame, text="Export CSV", command=self._export_csv, bootstyle="success").grid(row=0, column=2, sticky=E)

    def _load_columns(self) -> None:
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
                return

            # Initialize filtered columns (no filter applied initially)
            self.filtered_columns = self.df_columns.copy()
            
            # Initialize column variables for all columns
            self._initialize_column_vars()
            
            # Calculate pagination
            self._update_pagination()
            
            # Display first page
            self._populate_current_page()
            
        except Exception as e:
            Messagebox.show_error(f"Failed to load dataset columns: {str(e)}", title="Error")
            self.dialog.destroy()

    def _initialize_column_vars(self) -> None:
        """Initialize BooleanVar for all columns"""
        self.column_vars.clear()
        for col in self.df_columns:
            var = ttkb.BooleanVar(value=False)
            var.trace_add("write", self._update_selected_columns)
            self.column_vars[col] = var

    def _update_pagination(self) -> None:
        """Update pagination information based on filtered columns"""
        self.total_pages = max(1, math.ceil(len(self.filtered_columns) / self.columns_per_page))
        
        # Reset to first page if current page is out of bounds
        if self.current_page >= self.total_pages:
            self.current_page = 0
            
        self._update_pagination_controls()

    def _update_pagination_controls(self) -> None:
        """Update pagination control states and labels"""
        # Only update if UI elements have been created
        if not hasattr(self, 'page_label') or not hasattr(self, 'prev_btn') or not hasattr(self, 'next_btn'):
            return
            
        # Update page label
        self.page_label.config(text=f"Page {self.current_page + 1} of {self.total_pages}")
        
        # Update button states
        self.prev_btn.config(state=NORMAL if self.current_page > 0 else DISABLED)
        self.next_btn.config(state=NORMAL if self.current_page < self.total_pages - 1 else DISABLED)

    def _previous_page(self) -> None:
        """Navigate to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self._populate_current_page()
            self._update_pagination_controls()

    def _next_page(self) -> None:
        """Navigate to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._populate_current_page()
            self._update_pagination_controls()

    def _get_current_page_columns(self) -> List[str]:
        """Get columns for the current page"""
        start_idx = self.current_page * self.columns_per_page
        end_idx = start_idx + self.columns_per_page
        return self.filtered_columns[start_idx:end_idx]

    def _populate_current_page(self) -> None:
        """Populate the column list with current page columns"""
        # Don't populate if UI isn't ready yet
        if not hasattr(self, 'column_list_frame') or not self.column_list_frame.winfo_exists():
            return
            
        # Clear existing checkboxes
        for widget in self.column_list_frame.winfo_children():
            widget.destroy()
        self.column_checkboxes.clear()

        current_page_columns = self._get_current_page_columns()

        if not current_page_columns:
            # No columns to display
            no_cols_label = ttkb.Label(self.column_list_frame, text="No columns found", 
                                      font=("Segoe UI", 10), bootstyle="secondary")
            no_cols_label.pack(pady=20)
            return

        # Create a scrollable frame for checkboxes
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

        # Create checkboxes for current page columns only
        for col in current_page_columns:
            var = self.column_vars[col]  # Use existing BooleanVar
            cb = ttkb.Checkbutton(scrollable_frame, text=col, variable=var, bootstyle="round-toggle")
            cb.pack(anchor=W, pady=2)
            self.column_checkboxes[col] = cb

        # Bind mouse wheel scrolling (cross-platform) with proper focus handling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        def _bind_mousewheel(event):
            # Bind mouse wheel events when mouse enters the canvas area
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_linux)

        def _unbind_mousewheel(event):
            # Unbind mouse wheel events when mouse leaves the canvas area
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        # Bind enter/leave events to canvas and scrollable frame
        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)
        scrollable_frame.bind("<Enter>", _bind_mousewheel)
        scrollable_frame.bind("<Leave>", _unbind_mousewheel)

    def _filter_columns(self, *args) -> None:
        """Filter columns based on search term"""
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
        """Clear the search field"""
        self.column_search_var.set("")

    def _select_all_current_page(self) -> None:
        """Select all columns on the current page"""
        current_page_columns = self._get_current_page_columns()
        for col in current_page_columns:
            if col in self.column_vars:
                self.column_vars[col].set(True)

    def _select_all_filtered_columns(self) -> None:
        """Select all filtered columns (across all pages)"""
        for col in self.filtered_columns:
            if col in self.column_vars:
                self.column_vars[col].set(True)

    def _deselect_all_columns(self) -> None:
        """Deselect all columns"""
        for var in self.column_vars.values():
            var.set(False)

    def _update_selected_columns(self, *args) -> None:
        """Update the list of selected columns"""
        self.selected_columns = [col for col, var in self.column_vars.items() if var.get()]
        self._preview_export() # Update preview whenever column selection changes

    def _export_max_excel_rows(self) -> None:
        # Excel's row limit is 1,048,576
        self.row_selection_entry.delete(0, END)
        self.row_selection_entry.insert(0, "0-1048575") # Pythonic 0-indexed range

    def _parse_row_selection(self, selection_string: str) -> Optional[List[int]]:
        if not selection_string or selection_string == "Leave blank for all rows":
            return None # All rows

        rows = []
        parts = selection_string.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                try:
                    start_str, end_str = part.split('-')
                    start = int(start_str)
                    end = int(end_str)
                    if start > end:
                        raise ValueError("Start row cannot be greater than end row.")
                    rows.extend(range(start, end + 1))
                except ValueError:
                    Messagebox.show_error(f"Invalid range format: {part}", title="Input Error")
                    return []
            else:
                try:
                    rows.append(int(part))
                except ValueError:
                    Messagebox.show_error(f"Invalid row number: {part}", title="Input Error")
                    return []
        return sorted(list(set(rows))) # Remove duplicates and sort

    def _preview_export(self) -> None:
        selected_columns_count = len(self.selected_columns)
        row_selection_string = self.row_selection_entry.get()
        try:
            parsed_rows = self._parse_row_selection(row_selection_string)
            if parsed_rows is not None and not parsed_rows: # Error during parsing
                self.preview_label.config(text="Rows: Error × Columns: 0", bootstyle="danger")
                return

            estimated_rows = 0
            # Get total rows from dataset info (assuming a 'shape' attribute)
            info = self.file_handler.get_dataset_info(self.h5_file_path, self.dataset_path)
            total_dataset_rows = 0
            if 'shape' in info and isinstance(info['shape'], tuple) and len(info['shape']) > 0:
                total_dataset_rows = info['shape'][0]
            else:
                # If shape not directly available, try to infer from data for preview
                # This might involve reading a small part of the data which could be slow for very large files
                try:
                    sample_data, _ = self.file_handler.get_dataset_data(self.h5_file_path, self.dataset_path, max_elements=1) # Just get enough for shape
                    if isinstance(sample_data, pd.DataFrame):
                        total_dataset_rows = len(sample_data)
                    elif hasattr(sample_data, 'shape') and len(sample_data.shape) > 0:
                        total_dataset_rows = sample_data.shape[0]
                    else:
                        total_dataset_rows = 0
                except Exception:
                    total_dataset_rows = 0 # Cannot determine total rows reliably

            if parsed_rows is None:
                estimated_rows = total_dataset_rows
            else:
                # Filter parsed rows to be within dataset bounds
                valid_parsed_rows = [r for r in parsed_rows if r < total_dataset_rows]
                estimated_rows = len(valid_parsed_rows)

            self.preview_label.config(text=f"Rows: {estimated_rows:,} × Columns: {selected_columns_count}", bootstyle="primary")

        except Exception as e:
            self.preview_label.config(text=f"Error: {str(e)}", bootstyle="danger")

    def _export_csv(self) -> None:
        if not self.selected_columns:
            Messagebox.show_warning("Please select at least one column to export.", title="No Columns Selected")
            return

        row_selection_string = self.row_selection_entry.get()
        rows_to_export = self._parse_row_selection(row_selection_string)
        if rows_to_export == []: # Error during parsing
            return

        # Confirm export
        confirm_text = f"Proceed with exporting {self.preview_label['text']} to CSV?"
        if not Messagebox.okcancel(confirm_text, title="Confirm Export"):
            return

        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save CSV File As"
        )
        if not file_path:
            return # User cancelled

        try:
            self.dataframe_exporter.export_to_csv(
                h5_file_path=self.h5_file_path,
                dataset_path=self.dataset_path,
                columns=self.selected_columns,
                rows=rows_to_export,
                output_csv_path=file_path
            )
            Messagebox.show_info("Dataset exported successfully!", title="Export Complete")
        except Exception as e:
            Messagebox.show_error(f"Failed to export dataset: {str(e)}", title="Export Error")
        finally:
            self.dialog.destroy() # Close the export dialog