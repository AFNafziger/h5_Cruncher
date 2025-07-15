# core/h5_file_handler.py
import h5py
import numpy as np
import pandas as pd
from typing import List, Tuple, Any, Dict, Optional


class H5FileHandler:
    """Handles HDF5 file operations and data extraction"""

    def __init__(self):
        self.current_file_path = None

    def validate_file(self, file_path: str) -> bool:
        """
        Validate that the file is a valid HDF5 file

        Args:
            file_path: Path to the file to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with h5py.File(file_path, 'r') as f:
                # Just try to open it - if it works, it's valid
                pass
            return True
        except (OSError, ValueError):
            return False

    def get_datasets(self, file_path: str) -> List[str]:
        """
        Extract all dataset paths from an HDF5 file

        Args:
            file_path: Path to the HDF5 file

        Returns:
            List of dataset paths

        Raises:
            Exception: If file cannot be read
        """
        datasets = []

        def visit_func(name, obj):
            if isinstance(obj, h5py.Dataset):
                datasets.append(name)
            # Also consider groups that might represent dataframes
            # A common pattern for pandas HDFStore DataFrames is a group containing 'block*_items'
            elif isinstance(obj, h5py.Group) and any(key.startswith('block') and key.endswith('_items') for key in obj.keys()):
                datasets.append(name)


        try:
            with h5py.File(file_path, 'r') as f:
                f.visititems(visit_func)
            self.current_file_path = file_path
            return sorted(list(set(datasets))) # Return unique and sorted paths
        except Exception as e:
            raise Exception(f"Failed to read HDF5 file: {str(e)}")

    def get_dataset_info(self, file_path: str, dataset_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific dataset or group that represents a dataframe.

        Args:
            file_path: Path to the HDF5 file
            dataset_path: Path to the dataset or group within the file

        Returns:
            Dictionary with dataset information
        """
        info = {
            'path': dataset_path,
            'shape': 'N/A',
            'dtype': 'N/A',
            'size': 'N/A',
            'ndim': 'N/A',
            'maxshape': 'N/A',
            'chunks': 'N/A',
            'compression': 'N/A',
            'fillvalue': 'N/A',
            'attributes': {},
            'columns': [] # Add a key for columns
        }
        try:
            with h5py.File(file_path, 'r') as f:
                if dataset_path not in f:
                    raise ValueError(f"Object '{dataset_path}' not found in HDF5 file.")

                obj = f[dataset_path]

                if isinstance(obj, h5py.Dataset):
                    info['shape'] = obj.shape
                    info['dtype'] = str(obj.dtype)
                    info['size'] = obj.size
                    info['ndim'] = obj.ndim
                    info['maxshape'] = obj.maxshape
                    info['chunks'] = obj.chunks
                    info['compression'] = obj.compression
                    info['fillvalue'] = obj.fillvalue
                    # Add attributes
                    for key, value in obj.attrs.items():
                        info['attributes'][key] = value

                    # For single dataset, if it looks like a DataFrame, try to get columns
                    if info['ndim'] == 2 and (obj.dtype.fields is None): # Simple 2D array
                        info['columns'] = [f'Column_{i}' for i in range(info['shape'][1])]
                    elif obj.dtype.fields is not None: # Structured array
                         info['columns'] = list(obj.dtype.fields.keys())

                elif isinstance(obj, h5py.Group):
                    # This is where we try to infer if it's a pandas HDFStore dataframe
                    # or a similar tabular structure.
                    info['shape'] = 'Inferred'
                    info['dtype'] = 'Mixed/Inferred'
                    info['size'] = 'Inferred'
                    info['ndim'] = 'Inferred'

                    # Try to get columns for pandas HDFStore like groups
                    columns = self.get_dataframe_columns(file_path, dataset_path)
                    info['columns'] = columns

                    # Try to infer shape from block_values
                    inferred_rows = 0
                    inferred_cols = len(columns) if columns else 0

                    # Attempt to find shape from a block_values dataset
                    for key in obj.keys():
                        if key.startswith('block') and key.endswith('_values') and isinstance(obj[key], h5py.Dataset):
                            if len(obj[key].shape) > 0:
                                inferred_rows = max(inferred_rows, obj[key].shape[0])
                            # If it's a 1D block, its length is its "column"
                            if len(obj[key].shape) == 1 and inferred_cols == 0 and columns:
                                inferred_cols = len(columns)

                    if inferred_rows > 0:
                        # If a group represents a table, its first dimension is rows, second is columns
                        if inferred_cols > 0:
                            info['shape'] = (inferred_rows, inferred_cols)
                            info['size'] = inferred_rows * inferred_cols
                            info['ndim'] = 2 # Assuming 2D for tabular data
                        else: # Single column inferred or cannot determine columns
                            info['shape'] = (inferred_rows,)
                            info['size'] = inferred_rows
                            info['ndim'] = 1


                    # Add attributes for the group
                    for key, value in obj.attrs.items():
                        info['attributes'][key] = value

                else:
                    raise ValueError(f"Object '{dataset_path}' not found in HDF5 file.")
        except Exception as e:
            raise Exception(f"Failed to get dataset info for {dataset_path}: {str(e)}")
        return info

    def get_dataframe_columns(self, file_path: str, group_path: str) -> List[str]:
        """
        Attempts to infer DataFrame-like columns from an HDF5 group,
        especially for pandas HDFStore structures.
        Looks for 'axis0', 'block*_items' datasets.

        Args:
            file_path (str): Path to the HDF5 file.
            group_path (str): Path to the HDF5 group (e.g., 'x').

        Returns:
            List[str]: List of inferred column names.
        """
        columns = []
        try:
            with h5py.File(file_path, 'r') as hf:
                if group_path not in hf or not isinstance(hf[group_path], h5py.Group):
                    return [] # Not a group or doesn't exist

                group = hf[group_path]

                # 1. Try to read from 'axis0' if it exists and contains string data
                if 'axis0' in group and isinstance(group['axis0'], h5py.Dataset):
                    try:
                        # Decode byte strings if necessary
                        temp_cols = group['axis0'][()]
                        if temp_cols.dtype.kind == 'S': # Byte string
                            columns.extend([s.decode('utf-8') for s in temp_cols])
                        elif temp_cols.dtype.kind == 'U': # Unicode string
                            columns.extend(temp_cols)
                        elif temp_cols.dtype.kind == 'O' and isinstance(temp_cols, np.ndarray): # Object array
                            # Try to convert object array to string
                            for item in temp_cols:
                                if isinstance(item, bytes):
                                    columns.append(item.decode('utf-8'))
                                else:
                                    columns.append(str(item))

                        if columns:
                            return columns # Found columns from axis0

                    except Exception as e:
                        print(f"Warning: Could not read 'axis0' for columns in {group_path}: {e}")

                # 2. If 'axis0' didn't provide columns, look for 'blockX_items'
                block_item_columns = []
                for key in sorted(group.keys()): # Sort to ensure consistent order (block0, block1, etc.)
                    if key.startswith('block') and key.endswith('_items') and isinstance(group[key], h5py.Dataset):
                        try:
                            items_data = group[key][()]
                            if items_data.dtype.kind == 'S': # Byte string
                                block_item_columns.extend([s.decode('utf-8') for s in items_data])
                            elif items_data.dtype.kind == 'U': # Unicode string
                                block_item_columns.extend(items_data)
                            elif items_data.dtype.kind == 'O' and isinstance(items_data, np.ndarray): # Object array
                                for item in items_data:
                                    if isinstance(item, bytes):
                                        block_item_columns.append(item.decode('utf-8'))
                                    else:
                                        block_item_columns.append(str(item))

                        except Exception as e:
                            print(f"Warning: Could not read block_items '{key}' for columns in {group_path}: {e}")

                if block_item_columns:
                    return block_item_columns # Return columns found from block_items

                # 3. If it's a dataset and structured, get column names from dtype.fields
                if isinstance(group, h5py.Dataset) and group.dtype.fields is not None:
                    return list(group.dtype.fields.keys())

        except Exception as e:
            print(f"Error inferring dataframe columns for {group_path}: {e}")
        return []

    def read_dataset(self, file_path: str, dataset_path: str, slice_rows: Optional[Tuple[int, int]] = None) -> Any:
        """
        Reads a full dataset or a slice of it.
        This method will also attempt to reconstruct a pandas DataFrame if the
        dataset path points to an HDFStore-like group.

        Args:
            file_path (str): Path to the HDF5 file.
            dataset_path (str): Path to the dataset or group within the file.
            slice_rows (Optional[Tuple[int, int]]): A tuple (start_row, end_row)
                                                     for slicing. If None, read all.

        Returns:
            Any: The dataset data, potentially as a pandas DataFrame.
        """
        try:
            with h5py.File(file_path, 'r') as hf:
                if dataset_path not in hf:
                    raise ValueError(f"Object '{dataset_path}' not found in file.")

                obj = hf[dataset_path]

                if isinstance(obj, h5py.Dataset):
                    # For a direct dataset, read it as is
                    if slice_rows:
                        start, end = slice_rows
                        return obj[start:end]
                    else:
                        return obj[:]
                elif isinstance(obj, h5py.Group):
                    # This might be a pandas HDFStore DataFrame
                    # Attempt to reconstruct a DataFrame using pandas' own read_hdf
                    try:
                        df = pd.read_hdf(file_path, key=dataset_path, start=slice_rows[0] if slice_rows else None,
                                         stop=slice_rows[1] if slice_rows else None)
                        return df
                    except Exception as e:
                        # Fallback if pandas.read_hdf fails for some reason
                        print(f"Warning: Could not read group '{dataset_path}' directly as pandas HDF: {e}")
                        # If direct read_hdf fails, try to assemble from blocks.
                        # This part is more complex and depends heavily on pandas' internal HDFStore format.
                        # For now, if read_hdf fails, it implies a non-standard or complex HDFStore group.
                        raise ValueError(f"Group '{dataset_path}' is a complex HDF5 structure; direct DataFrame reconstruction failed.")
                else:
                    raise TypeError(f"Object at '{dataset_path}' is neither a Dataset nor a Group.")
        except Exception as e:
            raise Exception(f"Failed to read dataset/group data from {dataset_path}: {str(e)}")

    def get_dataset_data(self, file_path: str, dataset_path: str, max_elements: int = 1000) -> Tuple[Any, bool]:
        """
        Get a sample of dataset data for display, handling truncation.

        Args:
            file_path: Path to the HDF5 file
            dataset_path: Path to the dataset within the file
            max_elements: Maximum number of elements to retrieve

        Returns:
            Tuple: (data, is_truncated)
        """
        try:
            with h5py.File(file_path, 'r') as f:
                obj = f[dataset_path]
                is_truncated = False

                if isinstance(obj, h5py.Dataset):
                    # Check if the dataset is too large
                    if obj.size > max_elements:
                        is_truncated = True
                        if obj.ndim == 1:
                            return obj[:max_elements], True
                        elif obj.ndim == 2:
                            # For 2D, take first max_elements rows, all columns
                            if obj.shape[0] * obj.shape[1] > max_elements: # Check total elements, not just rows
                                return obj[:max_elements//obj.shape[1] if obj.shape[1] > 0 else 1, :], True # Take enough rows to meet max_elements
                            else:
                                return obj[:], False # Not truncated if fits
                        else:
                            # Multi-dimensional - flatten and take first max_elements
                            return obj.flat[:max_elements], True
                    else:
                        return obj[:], False
                elif isinstance(obj, h5py.Group):
                    # If it's a group representing a dataframe, try to read a sample using pandas
                    try:
                        df_sample = pd.read_hdf(file_path, key=dataset_path, stop=max_elements)
                        if df_sample.size > max_elements: # Check actual elements in sample vs max_elements
                            is_truncated = True
                        return df_sample, is_truncated
                    except Exception as e:
                        print(f"Warning: Could not read group '{dataset_path}' as pandas HDF for sample: {e}")
                        return f"Group: {dataset_path}. (Unable to display raw data as DataFrame.)", False
                else:
                    return "Unsupported HDF5 object type", False

        except Exception as e:
            raise Exception(f"Failed to read dataset data: {str(e)}")

    def is_string_dataset(self, file_path: str, dataset_path: str) -> bool:
        """
        Check if a dataset contains string data.
        Handles both h5py.Dataset and h5py.Group (for DataFrames).
        """
        try:
            with h5py.File(file_path, 'r') as f:
                obj = f[dataset_path]
                if isinstance(obj, h5py.Dataset):
                    return obj.dtype.kind in ('S', 'U', 'O')
                elif isinstance(obj, h5py.Group):
                    try:
                        # Try to load a small sample as DataFrame and check dtypes
                        df_sample = pd.read_hdf(file_path, key=dataset_path, stop=1)
                        return any(pd.api.types.is_string_dtype(df_sample[col]) for col in df_sample.columns)
                    except Exception as e:
                        # Fallback for groups not directly readable by pd.read_hdf
                        for key in obj.keys():
                            if key.endswith('_values') and isinstance(obj[key], h5py.Dataset):
                                if obj[key].dtype.kind in ('S', 'U', 'O'):
                                    return True
                    return False
        except Exception:
            return False

    def is_numeric_dataset(self, file_path: str, dataset_path: str) -> bool:
        """
        Check if a dataset contains numeric data.
        Handles both h5py.Dataset and h5py.Group (for DataFrames).
        """
        try:
            with h5py.File(file_path, 'r') as f:
                obj = f[dataset_path]
                if isinstance(obj, h5py.Dataset):
                    return np.issubdtype(obj.dtype, np.number)
                elif isinstance(obj, h5py.Group):
                    try:
                        # Try to load a small sample as DataFrame and check dtypes
                        df_sample = pd.read_hdf(file_path, key=dataset_path, stop=1)
                        return any(pd.api.types.is_numeric_dtype(df_sample[col]) for col in df_sample.columns)
                    except Exception as e:
                        # Fallback for groups not directly readable by pd.read_hdf
                        for key in obj.keys():
                            if key.endswith('_values') and isinstance(obj[key], h5py.Dataset):
                                if np.issubdtype(obj[key].dtype, np.number):
                                    return True
                    return False
        except Exception:
            return False