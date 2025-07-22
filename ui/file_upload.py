"""
File Upload UI Module
Handles the file upload interface and validation
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable, Optional
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *


class FileUpload:
    """Handles file upload UI and validation"""

    def __init__(self, parent: ttkb.Frame, callback: Callable[[str], None]):
        self.parent = parent
        self.callback = callback
        self.current_file: Optional[str] = None

        # UI elements
        self.upload_frame: Optional[ttkb.LabelFrame] = None
        self.file_label: Optional[ttkb.Label] = None
        self.upload_button: Optional[ttkb.Button] = None
        self.clear_button: Optional[ttkb.Button] = None

        # Store a consistent window size (optional if needed globally)
        self._set_minimum_parent_size()

    def _set_minimum_parent_size(self):
        # Delay until window is drawn
        self.parent.after(10, lambda: self.parent.winfo_toplevel().minsize(500, 150))

    def create_ui(self, row: int) -> None:
        """Create the file upload UI"""
        self.upload_frame = ttkb.LabelFrame(
            self.parent, text="File Upload", padding=15, bootstyle="info"
        )
        self.upload_frame.grid(row=row, column=0, sticky=(W, E), pady=(0, 20), padx=10)
        self.upload_frame.grid_columnconfigure(1, weight=1)

        self.upload_button = ttkb.Button(
            self.upload_frame,
            text="Select .h5 File",
            bootstyle="primary-outline",
            command=self._select_file
        )
        self.upload_button.grid(row=0, column=0, padx=(0, 10), sticky=W)

        self.file_label = ttkb.Label(
            self.upload_frame,
            text="No file selected",
            font=("Segoe UI", 9),
            bootstyle="secondary",
            anchor=W,
            width=50,  # fixed width in characters
            wraplength=400  # wrap long file names
        )
        self.file_label.grid(row=0, column=1, sticky=W)

        self.clear_button = ttkb.Button(
            self.upload_frame,
            text="✕ Clear",
            bootstyle="danger-outline",
            command=self._clear_file,
            state="disabled"
        )
        self.clear_button.grid(row=0, column=2, padx=(10, 0), sticky=E)

        hint_label = ttkb.Label(
            self.upload_frame,
            text="Supported format: HDF5 (.h5, .hdf5) files only",
            font=("Segoe UI", 8),
            bootstyle="secondary"
        )
        hint_label.grid(row=1, column=0, columnspan=3, sticky=W, pady=(8, 0))

        help_button = ttkb.Button(
            self.upload_frame,
            text="Help",
            bootstyle="info",
            command=self._open_help_window
        )
        help_button.grid(row=2, column=0, columnspan=3, sticky=W, pady=(10, 0))

    def _select_file(self) -> None:
        try:
            file_path = filedialog.askopenfilename(
                title="Select HDF5 File",
                filetypes=[
                    ("HDF5 files", "*.h5"),
                    ("HDF5 files", "*.hdf5"),
                    ("All files", "*.*")
                ],
                initialdir=Path.cwd()  # start in current directory
            )
            if file_path:
                self._process_file(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select file: {str(e)}")

    def _process_file(self, file_path: str) -> None:
        try:
            if not self._validate_file_extension(file_path):
                messagebox.showerror("Invalid File", "Please select a valid HDF5 file (.h5 or .hdf5)")
                return
            if not self._validate_file_access(file_path):
                messagebox.showerror("Access Error", "Cannot access the selected file. Please check permissions.")
                return
            self._update_file_status(file_path)
            self.callback(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {str(e)}")

    def _validate_file_extension(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in {'.h5', '.hdf5'}

    def _validate_file_access(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            return path.exists() and path.is_file() and path.stat().st_size > 0
        except:
            return False

    def _update_file_status(self, file_path: str) -> None:
        self.current_file = file_path
        file_name = Path(file_path).name
        file_size = self._get_file_size_str(file_path)
        self.file_label.config(
            text=f"✓ {file_name} ({file_size})",
            bootstyle="success"
        )
        self.clear_button.config(state="normal")
        self.upload_button.config(text="Change File")

    def _get_file_size_str(self, file_path: str) -> str:
        try:
            size = Path(file_path).stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Unknown size"

    def _clear_file(self) -> None:
        self.current_file = None
        self.file_label.config(text="No file selected", bootstyle="secondary")
        self.clear_button.config(state="disabled")
        self.upload_button.config(text="Select .h5 File")

    def get_current_file(self) -> Optional[str]:
        return self.current_file

    def set_file_programmatically(self, file_path: str) -> None:
        if self._validate_file_extension(file_path) and self._validate_file_access(file_path):
            self._process_file(file_path)
        else:
            raise ValueError(f"Invalid file path: {file_path}")
        
    def _open_help_window(self) -> None:
        root = self.parent.winfo_toplevel()
        help_win = ttkb.Toplevel(root)
        help_win.title("Help")
        help_win.geometry("500x300")
        help_win.resizable(True, True)
        help_win.transient(root)
        help_win.grab_set()

        # Center the help window
        help_win.update_idletasks()
        x = (help_win.winfo_screenwidth() // 2) - (help_win.winfo_width() // 2)
        y = (help_win.winfo_screenheight() // 2) - (help_win.winfo_height() // 2)
        help_win.geometry(f"+{x}+{y}")

        # Create a canvas and a vertical scrollbar for scrolling
        canvas = tk.Canvas(help_win, borderwidth=0, highlightthickness=0)
        vscroll = ttkb.Scrollbar(help_win, orient="vertical", command=canvas.yview)
        scrollable_frame = ttkb.Frame(canvas, padding=20)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=vscroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        help_label = ttkb.Label(
            scrollable_frame,
            text="Welcome to h5 Cruncher, a useful tool for exploring the unintuitive "
                 "structure of h5 files as well as exporting portions or special selections"
                 " of them to CSV files. To explore the structure of an h5 file, load the "
                 "file in the File Upload window and click around on the data frames that "
                 "appear BLUE may inform the column names of exportable data frames that do "
                 "not include them. \n\n Once you click on a GREEN dataframe, you will be given "
                 "three options of inspecting, exporting, or selecting a specific instance export."
                 "\n\nSpecific Instance Export Explained: Unsure of a better name to be honest. Specific instance export is used for creating a dataframe based on the value of a feature. For example, you have an h5 of cars with various features. You would use Specific Instance if you wanted to retrieve a CSV of just red cars along with their other atributes like make and model. Specific Instance Export takes a specific column with a specific value and creates a dataframe based on that."
                 "\n\nRegular exporting is simpler. Just select what columns you would like to have for your CSV and then optionally select which rows you would like, similar to selecting pages for a printer to print (typing \"1-100, 102, 104\" would give you 102 rows). "
                 "\n\nWhen working with large datasets, it can take a while exporting or sorting through values so please be patient.  ",
            font=("Segoe UI", 11),
            justify=LEFT,
            wraplength=450
        )
        help_label.pack(anchor=N, expand=True, fill="both")