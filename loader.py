import os
import stat

def select_h5_file():
    print("Enter the path to your H5 file:")
    file_path = input("File path: ").strip().strip('"').strip("'")
    
    if not os.path.exists(file_path):
        print("Cannot load: File not found")
        return None
    
    if not (file_path.lower().endswith('.h5') or file_path.lower().endswith('.hdf5')):
        print("Cannot load: Not an H5 file")
        return None
    
    return file_path

def protect_file_readonly(file_path):
    """Make file read-only to prevent modifications."""
    try:
        current_permissions = os.stat(file_path).st_mode
        readonly_permissions = current_permissions & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        os.chmod(file_path, readonly_permissions)
        print(f"File '{os.path.basename(file_path)}' is now read-only protected")
        return True
    except Exception as e:
        print(f"Error protecting file: {e}")
        return False

def main():#MAIN FUNCTION

    print(r"""
  _     _____    _____                       _               
 | |   | ____|  / ____|                     | |              
 | |__ | |__   | |     _ __ _   _ _ __   ___| |__   ___ _ __ 
 | '_ \|___ \  | |    | '__| | | | '_ \ / __| '_ \ / _ \ '__|
 | | | |___) | | |____| |  | |_| | | | | (__| | | |  __/ |   
 |_| |_|____/   \_____|_|   \__,_|_| |_|\___|_| |_|\___|_|   
 By Atticus Nafziger                                                             
 July 2025                                                           
""")
    print("-" * 20)
    
    file_path = select_h5_file()
    
    if not file_path:
        return
    
    print(f"Selected H5 file: {os.path.basename(file_path)}")
    
    if protect_file_readonly(file_path):
        print("File is protected and ready for processing")
        return file_path
    else:
        print("Failed to protect file")
        return None

if __name__ == "__main__":
    result = main()
    if result:
        print(f"Ready to process: {os.path.basename(result)}")
    else:
        print("\n Program terminated. Is your path correct? \n")