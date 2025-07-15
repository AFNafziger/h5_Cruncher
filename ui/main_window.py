import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog
from PIL import Image, ImageTk
from pathlib import Path
from typing import List, Optional

from core.h5_file_handler import H5FileHandler
from ui.dataset_inspector import DatasetInspector
from ui.dataset_list import DatasetList
from ui.file_upload import FileUpload
from ui.export_window import ExportWindow
from core.dataframe_exporter import DataFrameExporter

class MainWindow:
    def __init__(self, root: ttkb.Window):
        self.root = root
        self.current_file: Optional[str] = None
        self.datasets: List[str] = []

        self.file_handler = H5FileHandler()
        self.inspector = DatasetInspector(self.root)

        self._setup_window()
        self._setup_ui()
        self._center_window()

    def _setup_window(self) -> None:
        self.root.title("h5_cruncher2 - HDF5 Dataset Viewer")
        self.root.geometry("750x600")
        self.root.resizable(True, True)
        self.root.minsize(600, 400)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _setup_ui(self) -> None:
        main_frame = ttkb.Frame(self.root, padding=15)
        main_frame.grid(row=0, column=0, sticky=NSEW)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self._create_title(main_frame)

        self.file_upload = FileUpload(main_frame, self._on_file_uploaded)
        self.file_upload.create_ui(row=1)

        self.dataset_list = DatasetList(main_frame, self._on_dataset_selected)
        self.dataset_list.create_ui(row=2)

    def _create_title(self, parent: ttkb.Frame) -> None:
        title_frame = ttkb.Frame(parent)
        title_frame.grid(row=0, column=0, sticky=(W, E), pady=(0, 25))

        try:
            img = Image.open("assets/logo.png").resize((96, 96))
            self.logo_img = ImageTk.PhotoImage(img)
            img_label = ttkb.Label(title_frame, image=self.logo_img)
            img_label.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        except Exception as e:
            print("Logo failed to load:", e)

        #ttkb.Label(title_frame, text="h5_cruncher2",
        #           font=("Segoe UI", 20, "bold"), bootstyle="primary").grid(row=0, column=1, sticky=W)

        label_container = ttkb.Frame(title_frame)
        label_container.grid(row=0, column=1, sticky=W)

        # Title Label
        ttkb.Label(
            label_container,
            text="h5 CRUNCHER 2",
            font=("Segoe UI", 25, "bold"),
            bootstyle="primary"
        ).pack(anchor=W, pady=(0, 0))  # No padding between

        # Subtitle Label
        ttkb.Label(
            label_container,
            text="Curate, Review, Unpack, Navigate, Convert, Handle, Explore, Retrieve",
            font=("Segoe UI", 10),
            bootstyle="Dark"
        ).pack(anchor=W, pady=(0, 0))  # Still no padding

        ttkb.Label(
            label_container,
            text="Atticus Nafziger 2025",
            font=("Segoe UI", 10),
            bootstyle="secondary"
        ).pack(anchor=W, pady=(0, 0))  # Still no padding

    def _center_window(self) -> None:
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _on_file_uploaded(self, file_path: str) -> None:
        try:
            if not self.file_handler.validate_file(file_path):
                Messagebox.show_error("Invalid HDF5 file format", title="Error")
                return

            self.datasets = self.file_handler.get_datasets(file_path)
            self.current_file = file_path

            self.dataset_list.update_datasets(self.datasets)

            #Messagebox.show_info(f"Successfully loaded {len(self.datasets)} datasets", title="Success")

        except Exception as e:
            Messagebox.show_error(f"Failed to load file: {str(e)}", title="Error")

    def _on_dataset_selected(self, dataset_path: str) -> None:
        if not self.current_file:
            Messagebox.show_error("No file loaded", title="Error")
            return
        self._show_dataset_options(dataset_path)

    def _show_dataset_options(self, dataset_path: str) -> None:
        dialog = ttkb.Toplevel(self.root)
        dialog.title("Dataset Options")
        dialog.geometry("500x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        self._create_options_dialog_content(dialog, dataset_path)

    def _export_dataset(self, dataset_path: str, dialog: ttkb.Toplevel) -> None:
        dialog.destroy()
        if not self.current_file:
            Messagebox.show_error("No file loaded", title="Error")
            return
        # Instantiate and show the ExportWindow
        ExportWindow(self.root, self.current_file, dataset_path)

    def _create_options_dialog_content(self, dialog: ttkb.Toplevel, dataset_path: str) -> None:
        main_frame = ttkb.Frame(dialog, padding=25)
        main_frame.pack(fill=BOTH, expand=True)

        info_frame = ttkb.Frame(main_frame)
        info_frame.pack(fill=X, pady=(0, 20))

        ttkb.Label(info_frame, text="Selected Dataset:", font=("Segoe UI", 10, "bold")).pack(anchor=W)

        path_text = dataset_path if len(dataset_path) <= 60 else dataset_path[:57] + "..."
        ttkb.Label(info_frame, text=path_text, font=("Segoe UI", 10), bootstyle="info").pack(anchor=W, pady=(5, 0))

        try:
            info = self.file_handler.get_dataset_info(self.current_file, dataset_path)
            info_text = f"Shape: {info['shape']}, Type: {info['dtype']}, Size: {info['size']:,} elements"
            ttkb.Label(info_frame, text=info_text, font=("Segoe UI", 9), bootstyle="secondary").pack(anchor=W, pady=(5, 0))
        except:
            pass

        button_frame = ttkb.Frame(main_frame)
        button_frame.pack()

        ttkb.Button(button_frame, text="Inspect Dataset", bootstyle="success",
                    command=lambda: self._inspect_dataset(dataset_path, dialog)).pack(side=LEFT, padx=10)

        export_btn = ttkb.Button(button_frame, text="Export Dataset",
                             bootstyle="success",
                             command=lambda: self._export_dataset(dataset_path, dialog))
        export_btn.pack(side=LEFT, padx=10)

        instance_btn = ttkb.Button(button_frame, text="Specific Instance",
                                 bootstyle="success", state=DISABLED)
        instance_btn.pack(side=LEFT, padx=10)
        self._create_tooltip(instance_btn, "Instance functionality coming soon!")

        dialog.bind('<Return>', lambda e: self._inspect_dataset(dataset_path, dialog))
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    def _create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = ttkb.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttkb.Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1, padding=5)
            label.pack()
            tooltip.after(3000, tooltip.destroy)
            widget.tooltip = tooltip

        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')

        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def _inspect_dataset(self, dataset_path: str, dialog: ttkb.Toplevel) -> None:
        dialog.destroy()
        if not self.current_file:
            Messagebox.show_error("No file loaded", title="Error")
            return
        self.inspector.inspect_dataset(self.current_file, dataset_path)

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        self.inspector.close_inspector()
        self.root.quit()
        self.root.destroy()


if __name__ == "__main__":
    app = ttkb.Window(themename="darkly")
    main_window = MainWindow(app)
    main_window.run()
