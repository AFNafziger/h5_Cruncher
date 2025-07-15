#!/usr/bin/env python3
"""
h5_cruncher2 - A simple HDF5 dataset viewer and inspector
Author: Your Name
Platform: Linux (Boston University SCC)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import h5py
import numpy as np
from pathlib import Path
import traceback


class H5DatasetInspector:
    """Handles dataset inspection and display"""
    
    def __init__(self, parent):
        self.parent = parent
        self.inspector_window = None
    
    def inspect_dataset(self, file_path, dataset_path):
        """Open a new window to inspect the selected dataset"""
        try:
            with h5py.File(file_path, 'r') as f:
                dataset = f[dataset_path]
                
                # Get dataset information
                shape = dataset.shape
                dtype = dataset.dtype
                
                # Read data (be careful with large datasets)
                if dataset.size > 10000:  # Limit display for large datasets
                    data_preview = dataset.flat[:10000]
                    data_str = f"Dataset too large ({dataset.size} elements). Showing first 10,000 elements:\n\n"
                    data_str += str(np.array(data_preview).reshape(-1))
                    data_str += f"\n\n... ({dataset.size - 10000} more elements)"
                else:
                    data_str = str(dataset[...])
                
                # Create inspector window
                self._create_inspector_window(dataset_path, data_str, shape, dtype)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to inspect dataset: {str(e)}")
    
    def _create_inspector_window(self, dataset_path, data_str, shape, dtype):
        """Create and display the dataset inspector window"""
        # Close existing inspector window if open
        if self.inspector_window:
            self.inspector_window.destroy()
        
        # Create new window
        self.inspector_window = tk.Toplevel(self.parent)
        self.inspector_window.title(f"Dataset Inspector - {dataset_path}")
        self.inspector_window.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.inspector_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.inspector_window.grid_rowconfigure(0, weight=1)
        self.inspector_window.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Dataset info section
        info_frame = ttk.LabelFrame(main_frame, text="Dataset Information", padding="5")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(info_frame, text=dataset_path, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Shape:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(info_frame, text=str(shape), font=("TkDefaultFont", 9, "bold")).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(info_frame, text="Data Type:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(info_frame, text=str(dtype), font=("TkDefaultFont", 9, "bold")).grid(row=2, column=1, sticky=tk.W)
        
        # Data contents section
        ttk.Label(main_frame, text="Dataset Contents:", font=("TkDefaultFont", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        
        # Scrollable text area for data
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        data_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=("Courier", 9))
        data_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        data_text.insert(tk.END, data_str)
        data_text.config(state=tk.DISABLED)  # Make read-only
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.inspector_window.destroy).grid(row=3, column=0, pady=(10, 0))


class H5FileHandler:
    """Handles HDF5 file operations"""
    
    @staticmethod
    def get_datasets(file_path):
        """Extract all datasets from an HDF5 file"""
        datasets = []
        
        def visit_func(name, obj):
            if isinstance(obj, h5py.Dataset):
                datasets.append(name)
        
        try:
            with h5py.File(file_path, 'r') as f:
                f.visititems(visit_func)
        except Exception as e:
            raise Exception(f"Failed to read HDF5 file: {str(e)}")
        
        return sorted(datasets)


class H5Cruncher2:
    """Main application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("h5_cruncher2 - HDF5 Dataset Viewer")
        self.root.geometry("700x500")
        
        self.current_file = None
        self.datasets = []
        
        # Initialize components
        self.inspector = H5DatasetInspector(self.root)
        self.file_handler = H5FileHandler()
        
        # Setup UI
        self._setup_ui()
        
        # Center window on screen
        self._center_window()
    
    def _setup_ui(self):
        """Setup the main user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="h5_cruncher2", font=("TkDefaultFont", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # File upload section
        upload_frame = ttk.LabelFrame(main_frame, text="File Upload", padding="10")
        upload_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        upload_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Button(upload_frame, text="Upload .h5 File", command=self._upload_file).grid(row=0, column=0, padx=(0, 10))
        
        self.file_label = ttk.Label(upload_frame, text="No file selected", foreground="gray")
        self.file_label.grid(row=0, column=1, sticky=tk.W)
        
        # Dataset list section
        self.dataset_frame = ttk.LabelFrame(main_frame, text="Datasets", padding="10")
        self.dataset_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dataset_frame.grid_rowconfigure(0, weight=1)
        self.dataset_frame.grid_columnconfigure(0, weight=1)
        
        # Initially show "no file loaded" message
        self.no_file_label = ttk.Label(self.dataset_frame, text="Load an .h5 file to view datasets", 
                                      foreground="gray", font=("TkDefaultFont", 10, "italic"))
        self.no_file_label.grid(row=0, column=0)
        
        # Scrollable frame for dataset buttons (initially hidden)
        self.scroll_frame = None
    
    def _center_window(self):
        """Center the main window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _upload_file(self):
        """Handle file upload"""
        file_path = filedialog.askopenfilename(
            title="Select HDF5 file",
            filetypes=[("HDF5 files", "*.h5"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Validate file extension
                if not file_path.lower().endswith('.h5'):
                    messagebox.showerror("Error", "Please select a valid .h5 file")
                    return
                
                # Load datasets
                self.datasets = self.file_handler.get_datasets(file_path)
                self.current_file = file_path
                
                # Update UI
                self._update_file_label(file_path)
                self._create_dataset_buttons()
                
                messagebox.showinfo("Success", f"Loaded {len(self.datasets)} datasets from file")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def _update_file_label(self, file_path):
        """Update the file label with the selected file"""
        file_name = Path(file_path).name
        self.file_label.config(text=f"Loaded: {file_name}", foreground="green")
    
    def _create_dataset_buttons(self):
        """Create scrollable list of dataset buttons"""
        # Remove "no file" label
        self.no_file_label.grid_remove()
        
        # Remove existing scroll frame if present
        if self.scroll_frame:
            self.scroll_frame.destroy()
        
        # Create scrollable frame
        self.scroll_frame = ttk.Frame(self.dataset_frame)
        self.scroll_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scroll_frame.grid_rowconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(self.scroll_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.scroll_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid canvas and scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Create dataset buttons
        for i, dataset_path in enumerate(self.datasets):
            btn = ttk.Button(
                scrollable_frame,
                text=dataset_path,
                command=lambda path=dataset_path: self._show_dataset_options(path),
                width=60
            )
            btn.grid(row=i, column=0, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Configure scrollable frame
        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def _show_dataset_options(self, dataset_path):
        """Show options for the selected dataset"""
        # Create options dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Dataset Options - {dataset_path}")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        
        # Center dialog on parent
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Dataset label
        ttk.Label(main_frame, text=f"Selected dataset: {dataset_path}", 
                 font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, pady=(0, 20))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0)
        
        # Inspect button
        ttk.Button(button_frame, text="Inspect", 
                  command=lambda: self._inspect_dataset(dataset_path, dialog)).grid(row=0, column=0, padx=(0, 10))
        
        # Export button (disabled for now)
        export_btn = ttk.Button(button_frame, text="Export", state="disabled")
        export_btn.grid(row=0, column=1, padx=(10, 0))
        
        # Cancel button
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).grid(row=0, column=2, padx=(20, 0))
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def _inspect_dataset(self, dataset_path, dialog):
        """Inspect the selected dataset"""
        dialog.destroy()
        self.inspector.inspect_dataset(self.current_file, dataset_path)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    try:
        app = H5Cruncher2()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()