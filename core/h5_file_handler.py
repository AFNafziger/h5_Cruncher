"""
HDF5 File Handler Module
Handles all HDF5 file operations and data extraction
"""

import h5py
import numpy as np
from typing import List, Tuple, Any, Dict


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
        
        try:
            with h5py.File(file_path, 'r') as f:
                f.visititems(visit_func)
            self.current_file_path = file_path
        except Exception as e:
            raise Exception(f"Failed to read HDF5 file: {str(e)}")
        
        return sorted(datasets)
    
    def get_dataset_info(self, file_path: str, dataset_path: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a dataset
        
        Args:
            file_path: Path to the HDF5 file
            dataset_path: Path to the dataset within the file
            
        Returns:
            Dictionary containing dataset information
            
        Raises:
            Exception: If dataset cannot be accessed
        """
        try:
            with h5py.File(file_path, 'r') as f:
                dataset = f[dataset_path]
                
                info = {
                    'path': dataset_path,
                    'shape': dataset.shape,
                    'dtype': dataset.dtype,
                    'size': dataset.size,
                    'ndim': dataset.ndim,
                    'maxshape': dataset.maxshape,
                    'chunks': dataset.chunks,
                    'compression': dataset.compression,
                    'fillvalue': dataset.fillvalue,
                }
                
                # Add attributes if any
                if dataset.attrs:
                    info['attributes'] = dict(dataset.attrs)
                
                return info
                
        except Exception as e:
            raise Exception(f"Failed to get dataset info: {str(e)}")
    
    def get_dataset_data(self, file_path: str, dataset_path: str, 
                        max_elements: int = 10000) -> Tuple[Any, bool]:
        """
        Get dataset data with size limitations for display
        
        Args:
            file_path: Path to the HDF5 file
            dataset_path: Path to the dataset within the file
            max_elements: Maximum number of elements to return
            
        Returns:
            Tuple of (data, is_truncated)
            
        Raises:
            Exception: If dataset cannot be read
        """
        try:
            with h5py.File(file_path, 'r') as f:
                dataset = f[dataset_path]
                
                # Handle different data types and shapes
                if dataset.size == 0:
                    return None, False
                
                # For small datasets, return all data
                if dataset.size <= max_elements:
                    return dataset[...], False
                
                # For large datasets, return a sample
                if dataset.ndim == 1:
                    # 1D array - take first max_elements
                    return dataset[:max_elements], True
                elif dataset.ndim == 2:
                    # 2D array - take first rows up to max_elements total
                    rows_to_take = min(max_elements // dataset.shape[1], dataset.shape[0])
                    if rows_to_take > 0:
                        return dataset[:rows_to_take, :], True
                    else:
                        # If columns are too wide, take first column
                        return dataset[:, :1], True
                else:
                    # Multi-dimensional - flatten and take first max_elements
                    return dataset.flat[:max_elements], True
                    
        except Exception as e:
            raise Exception(f"Failed to read dataset data: {str(e)}")
    
    def is_string_dataset(self, file_path: str, dataset_path: str) -> bool:
        """
        Check if a dataset contains string data
        
        Args:
            file_path: Path to the HDF5 file
            dataset_path: Path to the dataset within the file
            
        Returns:
            bool: True if dataset contains strings
        """
        try:
            with h5py.File(file_path, 'r') as f:
                dataset = f[dataset_path]
                return dataset.dtype.kind in ('S', 'U', 'O')  # String types
        except:
            return False
    
    def is_numeric_dataset(self, file_path: str, dataset_path: str) -> bool:
        """
        Check if a dataset contains numeric data
        
        Args:
            file_path: Path to the HDF5 file
            dataset_path: Path to the dataset within the file
            
        Returns:
            bool: True if dataset contains numeric data
        """
        try:
            with h5py.File(file_path, 'r') as f:
                dataset = f[dataset_path]
                return np.issubdtype(dataset.dtype, np.number)
        except:
            return False