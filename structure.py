import os
import stat
from loader import main as load_h5_file

def display_file_stat(file_path):
    """Display basic file statistics using os.stat."""
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
        #print(f"Last modified: {time.ctime(st.st_mtime)}")
        #print(f"Last accessed: {time.ctime(st.st_atime)}")
        #print(f"Created: {time.ctime(st.st_ctime)}")
        print(f"{'='*50}")
    except Exception as e:
        print(f"Error reading file stats: {e}")

def main():
    """Main function to load and display file stats."""
    print("File Stat Viewer")
    print("-" * 40)
    
    file_path = load_h5_file()
    
    if file_path:
        display_file_stat(file_path)
    else:
        print("No file loaded for stat analysis")

if __name__ == "__main__":
    import time
    main()
