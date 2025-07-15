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
