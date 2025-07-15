import os
import stat
import h5py
from loader import main as load_h5_file

def display_file_stat(file_path):
    """Display basic file statistics using os.stat."""
    import time
    try:
        st = os.stat(file_path)
        size_bytes = st.st_size
        size_mb = size_bytes / (1024 * 1024)
        mode = stat.filemode(st.st_mode)
        print(f"\n{'='*50}")
        print(f"FILE: {os.path.basename(file_path)}")
        print(f"{'='*50}")
        print(f"Size: {size_bytes:,} bytes ({size_mb:.2f} MB)")
        print(f"Permissions: {mode}")
        print(f"Owner UID: {st.st_uid}")
        print(f"Group GID: {st.st_gid}")
        print(f"Last modified: {time.ctime(st.st_mtime)}")
        print(f"{'='*50}")
    except Exception as e:
        print(f"Error reading file stats: {e}")

def print_h5_structure(name, obj):
    """Helper function to print the structure of the HDF5 file."""
    if isinstance(obj, h5py.Group):
        print(f"[Group] {name}")
    elif isinstance(obj, h5py.Dataset):
        print(f"  [Dataset] {name} shape={obj.shape} dtype={obj.dtype}")

def display_h5_structure(file_path):
    """Display the internal structure of the HDF5 file."""
    print("\nHDF5 File Structure:")
    print("-" * 40)
    try:
        with h5py.File(file_path, 'r') as h5file:
            h5file.visititems(print_h5_structure)
    except Exception as e:
        print(f"Error reading HDF5 structure: {e}")

def main():
    """Main function to load and display file stats and structure."""
    print("HDF5 File Stat & Structure Viewer")
    print("-" * 40)
    
    file_path = load_h5_file()
    
    if file_path:
        display_file_stat(file_path)
        display_h5_structure(file_path)
    else:
        print("No file loaded for analysis")

if __name__ == "__main__":
    main()