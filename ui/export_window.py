# ui/export_window.py
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, END, W, E, NSEW, BOTH, LEFT, RIGHT, Y
import pandas as pd
import threading
import time
from typing import List, Optional, Tuple, Any

from core.h5_file_handler import H5FileHandler
from core.dataframe_exporter import DataFrameExporter


class ExportWindow:
    def __init__(self, master: ttkb.Window, h5_file_path: str, dataset_path: str):
        self.master = master
        self.h5_file_path = h5_file_path
        self.dataset_path = dataset_path
        self.file_handler = H5FileHandler()
        self.dataframe_exporter = DataFrameExporter()

        # Initialize all attributes first to prevent AttributeError
        self.df_columns: List[str] = []
        self.selected_columns: List[str] = []
        self.row_selection_string: str = ""
        self.column_selection_state: dict = {}  # {column_name: bool}
        self.column_checkboxes: dict = {}  # To store Checkbutton widgets
        self.column_vars: dict = {}  # To store BooleanVar for each checkbox
        
        # Add loading state management
        self.loading = False
        self.columns_loaded = False
        self.max_displayable_columns = 500  # Limit to prevent X11 memory issues

        self.dialog = ttkb.Toplevel(master)
        self.dialog.title(f"Export Dataset: {dataset_path.split('/')[-1]}")
        self.dialog.geometry("800x600")
        self.dialog.transient(master)
        self.dialog.grab_set()

        self._center_dialog()
        self._setup_ui()
        self._load_columns_safely()

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
        left_frame.grid_rowconfigure(3, weight=1)  # Make the scrollable area expandable
        left_frame.grid_columnconfigure(0, weight=1)

        ttkb.Label(left_frame, text="Select Columns:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky=W, pady=(0, 10))

        # Warning for large datasets
        self.warning_label = ttkb.Label(left_frame, text="", font=("Segoe UI", 9), bootstyle="warning")
        self.warning_label.grid(row=1, column=0, sticky=W, pady=(0, 5))

        # Search frame
        search_frame = ttkb.Frame(left_frame)
        search_frame.grid(row=2, column=0, sticky=(W, E), pady=(0, 10))
        search_frame.grid_columnconfigure(0, weight=1)

        self.column_search_var = ttkb.StringVar()
        # Don't trace immediately - wait until columns are loaded
        self.search_entry = ttkb.Entry(search_frame, textvariable=self.column_search_var, bootstyle="info")
        self.search_entry.grid(row=0, column=0, sticky=(W, E), padx=(0, 5))
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.insert(0, "Search columns...")
        self.search_entry.config(state="disabled")  # Initially disabled

        clear_search_btn = ttkb.Button(search_frame, text="✕", width=3, command=self._clear_search, state="disabled")
        clear_search_btn.grid(row=0, column=1)
        self.clear_search_btn = clear_search_btn

        # Scrollable column list frame
        self.column_list_container = ttkb.Frame(left_frame)
        self.column_list_container.grid(row=3, column=0, sticky=NSEW)
        self.column_list_container.grid_rowconfigure(0, weight=1)
        self.column_list_container.grid_columnconfigure(0, weight=1)

        # Create canvas and scrollbar for proper scrolling
        self.canvas = ttkb.Canvas(self.column_list_container, highlightthickness=0)
        self.scrollbar = ttkb.Scrollbar(self.column_list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttkb.Frame(self.canvas)

        # Configure scrolling properly
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Grid the canvas and scrollbar
        self.canvas.grid(row=0, column=0, sticky=NSEW)
        self.scrollbar.grid(row=0, column=1, sticky=(N, S))

        # Configure the scrollable frame to expand
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Bind mouse wheel to canvas
        self._bind_mouse_wheel()

        # Loading indicator
        self.loading_label = ttkb.Label(self.scrollable_frame, text="Loading columns...", 
                                       font=("Segoe UI", 10), bootstyle="info")
        self.loading_label.grid(row=0, column=0, pady=20)

        # Selection controls
        selection_frame = ttkb.Frame(left_frame)
        selection_frame.grid(row=4, column=0, sticky=(W, E), pady=(10, 0))
        selection_frame.grid_columnconfigure(0, weight=1)
        selection_frame.grid_columnconfigure(1, weight=1)

        self.select_all_button = ttkb.Button(selection_frame, text="Select All", 
                                           command=self._select_all_filtered_columns, 
                                           bootstyle="info-outline", state="disabled")
        self.select_all_button.grid(row=0, column=0, sticky=EW, padx=(0, 5))

        self.select_none_button = ttkb.Button(selection_frame, text="Select None", 
                                            command=self._select_none, 
                                            bootstyle="secondary-outline", state="disabled")
        self.select_none_button.grid(row=0, column=1, sticky=EW, padx=(5, 0))

        # Right Panel: Value Selector (Rows)
        right_frame = ttkb.Frame(main_frame, relief="solid", borderwidth=1, padding=10)
        right_frame.grid(row=0, column=1, sticky=NSEW, padx=(10, 0))
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        ttkb.Label(right_frame, text="Select Rows (e.g., 1-10,12,200)", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky=W, pady=(0, 10))
        self.row_selection_entry = ttkb.Entry(right_frame, bootstyle="info")
        self.row_selection_entry.grid(row=1, column=0, sticky=EW, pady=(0, 10))
        self.row_selection_entry.insert(0, "Leave blank for all rows")
        self.row_selection_entry.configure(foreground="grey")
        self.row_selection_entry.bind("<FocusIn>", self._on_row_focus_in)

        ttkb.Label(right_frame, text="Excel's row limit is 1,048,576 rows.", font=("Segoe UI", 9), bootstyle="warning").grid(row=2, column=0, sticky=W, pady=(5, 0))

        export_max_rows_btn = ttkb.Button(right_frame, text="Export Max Excel Rows", command=self._export_max_excel_rows, bootstyle="info-outline")
        export_max_rows_btn.grid(row=3, column=0, sticky=EW, pady=(10, 0))

        # Dataset info section
        info_frame = ttkb.LabelFrame(right_frame, text="Dataset Info", padding=10)
        info_frame.grid(row=4, column=0, sticky=(W, E), pady=(15, 0))
        
        self.dataset_info_label = ttkb.Label(info_frame, text="Loading dataset info...", 
                                           font=("Segoe UI", 9), bootstyle="secondary")
        self.dataset_info_label.pack(anchor=W)

        # Bottom Panel: Export and Info
        bottom_frame = ttkb.Frame(main_frame, padding=(0, 10))
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky=EW)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, weight=1)

        self.preview_label = ttkb.Label(bottom_frame, text="Rows: 0 × Columns: 0", font=("Segoe UI", 10))
        self.preview_label.grid(row=0, column=0, sticky=W)

        self.preview_button = ttkb.Button(bottom_frame, text="Preview", command=self._preview_export, 
                                        bootstyle="secondary", state="disabled")
        self.preview_button.grid(row=0, column=1, sticky=EW, padx=10)
        
        self.export_button = ttkb.Button(bottom_frame, text="Export CSV", command=self._export_csv, 
                                       bootstyle="success", state="disabled")
        self.export_button.grid(row=0, column=2, sticky=E)

    def _on_search_focus_in(self, event):
        if self.search_entry.get() == "Search columns...":
            self.search_entry.delete(0, END)

    def _on_row_focus_in(self, event):
        if self.row_selection_entry.get() == "Leave blank for all rows":
            self.row_selection_entry.delete(0, END)

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

    def _clear_search(self) -> None:
        """Clear the search field"""
        if self.columns_loaded:
            self.column_search_var.set("")

    def _load_columns_safely(self) -> None:
        """Load columns in a separate thread to prevent UI freezing"""
        if self.loading:
            return
        
        self.loading = True
        
        def load_columns_thread():
            try:
                # Load dataset info first (this is usually fast)
                info = self.file_handler.get_dataset_info(self.h5_file_path, self.dataset_path)
                
                # Update dataset info in UI thread
                self.dialog.after(0, lambda: self._update_dataset_info(info))
                
                # Get columns (this might be slow for large datasets)
                if 'columns' in info and info['columns']:
                    columns = info['columns']
                else:
                    # Fallback: try to get columns by reading a small sample
                    try:
                        sample_data = self.file_handler.read_dataset(
                            self.h5_file_path, self.dataset_path, slice_rows=(0, 1)
                        )
                        if isinstance(sample_data, pd.DataFrame):
                            columns = sample_data.columns.tolist()
                        else:
                            columns = []
                    except Exception as e:
                        print(f"Error getting sample data: {e}")
                        columns = []
                
                # Update UI in main thread
                self.dialog.after(0, lambda: self._on_columns_loaded(columns))
                
            except Exception as e:
                # Handle error in main thread
                self.dialog.after(0, lambda: self._on_columns_load_error(str(e)))
        
        # Start loading in background thread
        thread = threading.Thread(target=load_columns_thread, daemon=True)
        thread.start()

    def _update_dataset_info(self, info: dict) -> None:
        """Update the dataset info display"""
        try:
            shape = info.get('shape', 'Unknown')
            dtype = info.get('dtype', 'Unknown')
            size = info.get('size', 'Unknown')
            
            if isinstance(size, int):
                size_str = f"{size:,}"
            else:
                size_str = str(size)
            
            info_text = f"Shape: {shape}\nType: {dtype}\nElements: {size_str}"
            self.dataset_info_label.config(text=info_text)
        except Exception as e:
            self.dataset_info_label.config(text=f"Error loading info: {str(e)}")

    def _on_columns_loaded(self, columns: List[str]) -> None:
        """Called when columns are successfully loaded"""
        try:
            self.df_columns = columns
            self.columns_loaded = True
            self.loading = False
            
            # Initialize selection state for all columns (all unselected by default)
            for col in self.df_columns:
                if col not in self.column_selection_state:
                    self.column_selection_state[col] = False

            if not self.df_columns:
                self.loading_label.config(text="No columns found in dataset", bootstyle="warning")
                return
            
            # Check if we have too many columns to display safely
            if len(self.df_columns) > self.max_displayable_columns:
                self.warning_label.config(
                    text=f"⚠️ Large dataset ({len(self.df_columns)} columns). Use search to filter.", 
                    bootstyle="warning"
                )
                # Hide loading label and show search instruction
                self.loading_label.config(
                    text=f"Dataset has {len(self.df_columns)} columns.\nUse search above to filter columns before displaying.",
                    bootstyle="info"
                )
                
                # Enable search but don't populate all columns yet
                self.search_entry.config(state="normal")
                self.clear_search_btn.config(state="normal")
                
                # Set up search trace now that columns are loaded
                self.column_search_var.trace_add("write", self._filter_columns)
                
                # Enable other controls
                self.preview_button.config(state="normal")
                self.export_button.config(state="normal")
                
            else:
                # Small dataset - can display all columns
                self.loading_label.destroy()
                self._populate_column_list(self.df_columns)
                
                # Enable all UI elements
                self.search_entry.config(state="normal")
                self.clear_search_btn.config(state="normal")
                self.select_all_button.config(state="normal")
                self.select_none_button.config(state="normal")
                self.preview_button.config(state="normal")
                self.export_button.config(state="normal")
                
                # Set up search trace now that columns are loaded
                self.column_search_var.trace_add("write", self._filter_columns)
            
        except Exception as e:
            self._on_columns_load_error(str(e))

    def _on_columns_load_error(self, error_msg: str) -> None:
        """Called when there's an error loading columns"""
        self.loading = False
        self.loading_label.config(text=f"Error loading columns: {error_msg}", bootstyle="danger")
        
        # Show error dialog
        Messagebox.show_error(
            f"Failed to load dataset columns: {error_msg}\n\n"
            "This might be due to:\n"
            "• Very large dataset size\n"
            "• Unsupported dataset format\n"
            "• Memory limitations",
            title="Error Loading Dataset"
        )

    def _populate_column_list(self, columns_to_display: List[str]) -> None:
        """Populate the column list with safety limits"""
        if not self.columns_loaded:
            return
        
        # Safety check - don't display too many columns at once
        if len(columns_to_display) > self.max_displayable_columns:
            # Show truncated message instead of creating thousands of widgets
            self._show_truncated_message(len(columns_to_display))
            return
            
        # Save current selection state before clearing
        self._save_current_selection_state()
        
        # Clear existing checkboxes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.column_checkboxes.clear()
        self.column_vars.clear()

        # Create checkboxes for the filtered columns
        for i, col in enumerate(columns_to_display):
            # Use the persistent selection state
            initial_value = self.column_selection_state.get(col, False)
            var = ttkb.BooleanVar(value=initial_value)
            cb = ttkb.Checkbutton(self.scrollable_frame, text=col, variable=var, bootstyle="round-toggle")
            cb.grid(row=i, column=0, sticky=W, pady=1, padx=5)
            
            self.column_checkboxes[col] = cb
            self.column_vars[col] = var
            # Add a trace to update selected_columns on change
            var.trace_add("write", self._update_selected_columns)
        
        # Update the canvas scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # Enable selection buttons
        self.select_all_button.config(state="normal")
        self.select_none_button.config(state="normal")
        
        self._update_selected_columns()

    def _show_truncated_message(self, total_columns: int) -> None:
        """Show message when too many columns to display"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.column_checkboxes.clear()
        self.column_vars.clear()
        
        # Show informative message
        msg_label = ttkb.Label(
            self.scrollable_frame, 
            text=f"Too many columns to display ({total_columns} total).\n\n"
                 "Please use the search box above to filter columns.\n"
                 "Example searches:\n"
                 "• 'gene' - shows columns containing 'gene'\n"
                 "• 'cell_' - shows columns starting with 'cell_'\n"
                 "• '001' - shows columns containing '001'",
            font=("Segoe UI", 10), 
            bootstyle="info",
            justify="left"
        )
        msg_label.grid(row=0, column=0, pady=20, padx=10, sticky=W)

    def _save_current_selection_state(self) -> None:
        """Save the current selection state before rebuilding the list"""
        for col, var in self.column_vars.items():
            self.column_selection_state[col] = var.get()

    def _filter_columns(self, *args) -> None:
        if not self.columns_loaded:
            return
            
        search_term = self.column_search_var.get().lower()
        if search_term == "search columns...":
            search_term = ""
        
        if not search_term:
            # No search term - only show all if dataset is small enough
            if len(self.df_columns) <= self.max_displayable_columns:
                filtered_columns = self.df_columns
            else:
                # Too many columns - show none until user searches
                filtered_columns = []
        else:
            # Filter columns based on search
            filtered_columns = [col for col in self.df_columns if search_term in col.lower()]
            # Still limit the results to prevent UI overload
            if len(filtered_columns) > self.max_displayable_columns:
                filtered_columns = filtered_columns[:self.max_displayable_columns]
                # Update warning to show truncation
                self.warning_label.config(
                    text=f"Showing first {self.max_displayable_columns} of {len([col for col in self.df_columns if search_term in col.lower()])} matches", 
                    bootstyle="warning"
                )
            else:
                self.warning_label.config(text="")
        
        self._populate_column_list(filtered_columns)

    def _update_selected_columns(self, *args) -> None:
        # Update the persistent state and the selected columns list
        for col, var in self.column_vars.items():
            self.column_selection_state[col] = var.get()
        
        self.selected_columns = [col for col, selected in self.column_selection_state.items() if selected]
        self._preview_export() # Update preview whenever column selection changes

    def _select_all_filtered_columns(self) -> None:
        if not self.columns_loaded:
            return
            
        for col, var in self.column_vars.items():
            var.set(True)
            self.column_selection_state[col] = True
        
        self._update_selected_columns()

    def _select_none(self) -> None:
        if not self.columns_loaded:
            return
            
        for col, var in self.column_vars.items():
            var.set(False)
            self.column_selection_state[col] = False
        
        self._update_selected_columns()

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
        if not self.columns_loaded:
            self.preview_label.config(text="Loading...", bootstyle="info")
            return
            
        selected_columns_count = len(self.selected_columns)
        row_selection_string = self.row_selection_entry.get()
        try:
            parsed_rows = self._parse_row_selection(row_selection_string)
            if parsed_rows is not None and not parsed_rows: # Error during parsing
                self.preview_label.config(text="Rows: Error × Columns: 0", bootstyle="danger")
                return

            # Get total rows from dataset info without loading data
            try:
                info = self.file_handler.get_dataset_info(self.h5_file_path, self.dataset_path)
                total_dataset_rows = 0
                if 'shape' in info and isinstance(info['shape'], tuple) and len(info['shape']) > 0:
                    total_dataset_rows = info['shape'][0]
                else:
                    total_dataset_rows = 0  # Cannot determine reliably without loading data
            except Exception:
                total_dataset_rows = 0

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
        if not self.columns_loaded:
            Messagebox.show_warning("Columns are still loading. Please wait.", title="Still Loading")
            return
            
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

        # Show progress dialog and start export in background
        self._show_export_progress(file_path, rows_to_export)

    def _show_export_progress(self, output_path: str, rows_to_export: Optional[List[int]]) -> None:
        """Show export progress dialog and handle export in background thread"""
        # Create progress dialog
        self.progress_dialog = ttkb.Toplevel(self.dialog)
        self.progress_dialog.title("Exporting CSV...")
        self.progress_dialog.geometry("500x200")
        self.progress_dialog.transient(self.dialog)
        self.progress_dialog.grab_set()
        self.progress_dialog.resizable(False, False)
        
        # Center the progress dialog
        self.progress_dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (250)
        y = (self.dialog.winfo_screenheight() // 2) - (100)
        self.progress_dialog.geometry(f"+{x}+{y}")
        
        # Progress dialog content
        progress_frame = ttkb.Frame(self.progress_dialog, padding=20)
        progress_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = ttkb.Label(progress_frame, text="Exporting Dataset to CSV", 
                                font=("Segoe UI", 12, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Status label
        self.status_label = ttkb.Label(progress_frame, text="Initializing export...", 
                                      font=("Segoe UI", 10))
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = ttkb.DoubleVar()
        self.progress_bar = ttkb.Progressbar(progress_frame, variable=self.progress_var, 
                                           length=400, mode='determinate')
        self.progress_bar.pack(pady=(0, 10))
        
        # Percentage label
        self.percentage_label = ttkb.Label(progress_frame, text="0%", 
                                          font=("Segoe UI", 9))
        self.percentage_label.pack(pady=(0, 15))
        
        # Cancel button
        self.cancel_export = False
        cancel_button = ttkb.Button(progress_frame, text="Cancel", 
                                   command=self._cancel_export, bootstyle="danger-outline")
        cancel_button.pack()
        
        # Start export in background thread
        self.export_thread = threading.Thread(
            target=self._export_worker, 
            args=(output_path, rows_to_export),
            daemon=True
        )
        self.export_thread.start()
        
        # Monitor progress
        self._monitor_export_progress()

    def _cancel_export(self) -> None:
        """Cancel the ongoing export"""
        self.cancel_export = True
        self.status_label.config(text="Cancelling export...", bootstyle="warning")

    def _export_worker(self, output_path: str, rows_to_export: Optional[List[int]]) -> None:
        """Worker thread that performs the actual export with progress updates"""
        try:
            # Update status
            self.dialog.after(0, lambda: self.status_label.config(text="Reading dataset..."))
            self.dialog.after(0, lambda: self._update_progress(10, "Loading data from HDF5 file..."))
            
            # Check for cancellation
            if self.cancel_export:
                return
            
            # Read the dataset
            if rows_to_export is not None and len(rows_to_export) > 0:
                # Check if rows are a continuous slice for efficiency
                is_continuous_slice = (len(rows_to_export) > 0 and
                                     all(rows_to_export[i] + 1 == rows_to_export[i+1] 
                                         for i in range(len(rows_to_export)-1)))
                if is_continuous_slice:
                    start_row = min(rows_to_export)
                    end_row = max(rows_to_export) + 1
                    data_df = self.file_handler.read_dataset(
                        self.h5_file_path, self.dataset_path, slice_rows=(start_row, end_row)
                    )
                else:
                    # Read full dataset and filter
                    data_df = self.file_handler.read_dataset(self.h5_file_path, self.dataset_path)
                    if not self.cancel_export:
                        self.dialog.after(0, lambda: self._update_progress(30, "Filtering selected rows..."))
                        data_df = data_df.iloc[rows_to_export]
            else:
                # Read all data
                data_df = self.file_handler.read_dataset(self.h5_file_path, self.dataset_path)
            
            if self.cancel_export:
                return
                
            # Validate data type
            if not isinstance(data_df, pd.DataFrame):
                raise TypeError("Data read from HDF5 file is not a pandas DataFrame.")
            
            self.dialog.after(0, lambda: self._update_progress(50, "Filtering selected columns..."))
            
            # Filter columns
            existing_columns = [col for col in self.selected_columns if col in data_df.columns]
            if len(existing_columns) != len(self.selected_columns):
                missing_cols = set(self.selected_columns) - set(existing_columns)
                print(f"Warning: Missing columns will be skipped: {missing_cols}")
            
            data_df = data_df[existing_columns]
            
            if self.cancel_export:
                return
            
            self.dialog.after(0, lambda: self._update_progress(70, "Writing CSV file..."))
            
            # Export to CSV with progress monitoring for large files
            if len(data_df) > 100000:  # For large datasets, use chunked writing
                self._export_large_csv(data_df, output_path)
            else:
                data_df.to_csv(output_path, index=False)
                self.dialog.after(0, lambda: self._update_progress(100, "Export completed successfully!"))
            
            # Success
            if not self.cancel_export:
                self.dialog.after(0, self._export_success)
                
        except Exception as e:
            if not self.cancel_export:
                error_msg = str(e)
                self.dialog.after(0, lambda: self._export_error(error_msg))

    def _export_large_csv(self, data_df: pd.DataFrame, output_path: str) -> None:
        """Export large dataframes in chunks with progress updates"""
        chunk_size = 50000  # Write 50k rows at a time
        total_rows = len(data_df)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            # Write header
            data_df.head(0).to_csv(f, index=False)
            
            # Write data in chunks
            for i in range(0, total_rows, chunk_size):
                if self.cancel_export:
                    return
                    
                end_idx = min(i + chunk_size, total_rows)
                chunk = data_df.iloc[i:end_idx]
                
                # Write chunk (without header since we already wrote it)
                chunk.to_csv(f, mode='a', header=False, index=False)
                
                # Update progress
                progress = 70 + (30 * (end_idx / total_rows))  # 70-100% range
                rows_written = end_idx
                status_text = f"Writing CSV... ({rows_written:,} / {total_rows:,} rows)"
                self.dialog.after(0, lambda p=progress, s=status_text: self._update_progress(p, s))
        
        if not self.cancel_export:
            self.dialog.after(0, lambda: self._update_progress(100, "Export completed successfully!"))

    def _update_progress(self, percentage: float, status_text: str) -> None:
        """Update progress bar and status text"""
        self.progress_var.set(percentage)
        self.percentage_label.config(text=f"{percentage:.0f}%")
        self.status_label.config(text=status_text)

    def _monitor_export_progress(self) -> None:
        """Monitor the export thread and handle completion"""
        if self.export_thread.is_alive():
            # Check again in 100ms
            self.dialog.after(100, self._monitor_export_progress)
        else:
            # Thread finished, but don't close dialog yet - let success/error handlers do it
            pass

    def _export_success(self) -> None:
        """Handle successful export completion"""
        self.progress_dialog.destroy()
        Messagebox.show_info("Dataset exported successfully!", title="Export Complete")
        self.dialog.destroy()  # Close the main export dialog

    def _export_error(self, error_msg: str) -> None:
        """Handle export error"""
        self.progress_dialog.destroy()
        Messagebox.show_error(f"Failed to export dataset: {error_msg}", title="Export Error")
        # Don't close the main dialog so user can try again