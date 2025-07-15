"""
Data Formatter Module
Handles formatting of dataset data for display in different formats
"""

import numpy as np
from typing import Any, Tuple, List


class DataFormatter:
    """Handles formatting of dataset data for display purposes"""
    
    @staticmethod
    def format_for_display(data: Any, is_truncated: bool, original_shape: Tuple, 
                          max_display_width: int = 80) -> str:
        """
        Format data for display in the inspector
        
        Args:
            data: The dataset data
            is_truncated: Whether the data was truncated
            original_shape: Original shape of the dataset
            max_display_width: Maximum width for display lines
            
        Returns:
            Formatted string for display
        """
        if data is None:
            return "Empty dataset"
        
        # Convert to numpy array if not already
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        
        # Handle different data types
        if data.dtype.kind in ('S', 'U'):  # String data
            return DataFormatter._format_string_data(data, is_truncated, original_shape)
        elif np.issubdtype(data.dtype, np.number):  # Numeric data
            return DataFormatter._format_numeric_data(data, is_truncated, original_shape, max_display_width)
        else:  # Other data types
            return DataFormatter._format_generic_data(data, is_truncated, original_shape, max_display_width)
    
    @staticmethod
    def _format_string_data(data: np.ndarray, is_truncated: bool, original_shape: Tuple) -> str:
        """Format string data for display"""
        if data.ndim == 1:
            # 1D string array - display as vertical column
            result = "String Values:\n" + "-" * 50 + "\n"
            for i, item in enumerate(data):
                # Decode bytes to string if necessary
                if isinstance(item, bytes):
                    item = item.decode('utf-8', errors='replace')
                result += f"[{i:4d}]  {item}\n"
            
            if is_truncated:
                result += f"\n... (showing first {len(data)} of {np.prod(original_shape)} total elements)"
            
            return result
        
        elif data.ndim == 2:
            # 2D string array - display as table
            result = "String Array (2D):\n" + "-" * 50 + "\n"
            for i, row in enumerate(data):
                row_str = "  ".join([
                    (item.decode('utf-8', errors='replace') if isinstance(item, bytes) else str(item))[:20]
                    for item in row
                ])
                result += f"[{i:4d}]  {row_str}\n"
            
            if is_truncated:
                result += f"\n... (showing first {data.shape[0]} rows of {original_shape[0]} total rows)"
            
            return result
        
        else:
            # Multi-dimensional - flatten and display
            flattened = data.flatten()
            result = f"String Array ({data.ndim}D, flattened view):\n" + "-" * 50 + "\n"
            for i, item in enumerate(flattened):
                if isinstance(item, bytes):
                    item = item.decode('utf-8', errors='replace')
                result += f"[{i:4d}]  {item}\n"
            
            if is_truncated:
                result += f"\n... (showing first {len(flattened)} of {np.prod(original_shape)} total elements)"
            
            return result
    
    @staticmethod
    def _format_numeric_data(data: np.ndarray, is_truncated: bool, original_shape: Tuple, 
                           max_display_width: int) -> str:
        """Format numeric data for display"""
        if data.ndim == 1:
            # 1D numeric array - display as vertical column
            result = "Numeric Values:\n" + "-" * 50 + "\n"
            for i, item in enumerate(data):
                # Format numbers appropriately
                if np.issubdtype(data.dtype, np.integer):
                    result += f"[{i:4d}]  {item}\n"
                elif np.issubdtype(data.dtype, np.floating):
                    result += f"[{i:4d}]  {item:.6g}\n"
                else:
                    result += f"[{i:4d}]  {item}\n"
            
            if is_truncated:
                result += f"\n... (showing first {len(data)} of {np.prod(original_shape)} total elements)"
            
            return result
        
        elif data.ndim == 2:
            # 2D numeric array - display as formatted table
            result = "Numeric Array (2D):\n" + "-" * 50 + "\n"
            
            # Calculate column widths
            col_widths = []
            for col in range(data.shape[1]):
                max_width = max(len(f"{item:.6g}" if np.issubdtype(data.dtype, np.floating) 
                                   else str(item)) for item in data[:, col])
                col_widths.append(min(max_width, 15))  # Cap at 15 characters
            
            # Format each row
            for i, row in enumerate(data):
                row_parts = []
                for j, item in enumerate(row):
                    if np.issubdtype(data.dtype, np.floating):
                        formatted = f"{item:.6g}".rjust(col_widths[j])
                    else:
                        formatted = str(item).rjust(col_widths[j])
                    row_parts.append(formatted)
                
                result += f"[{i:4d}]  " + "  ".join(row_parts) + "\n"
            
            if is_truncated:
                result += f"\n... (showing first {data.shape[0]} rows of {original_shape[0]} total rows)"
            
            return result
        
        else:
            # Multi-dimensional - show summary and some values
            result = f"Numeric Array ({data.ndim}D):\n" + "-" * 50 + "\n"
            result += f"Shape: {data.shape}\n"
            result += f"Min: {np.min(data):.6g}\n"
            result += f"Max: {np.max(data):.6g}\n"
            result += f"Mean: {np.mean(data):.6g}\n"
            result += f"Std: {np.std(data):.6g}\n\n"
            
            # Show some flattened values
            flattened = data.flatten()
            result += "Sample values (flattened):\n"
            for i, item in enumerate(flattened[:100]):  # Show first 100
                if np.issubdtype(data.dtype, np.floating):
                    result += f"[{i:4d}]  {item:.6g}\n"
                else:
                    result += f"[{i:4d}]  {item}\n"
            
            if len(flattened) > 100:
                result += f"... (showing first 100 of {len(flattened)} total elements)"
            
            return result
    
    @staticmethod
    def _format_generic_data(data: np.ndarray, is_truncated: bool, original_shape: Tuple, 
                           max_display_width: int) -> str:
        """Format generic data types for display"""
        if data.ndim == 1:
            # 1D array - display as vertical column
            result = "Dataset Values:\n" + "-" * 50 + "\n"
            for i, item in enumerate(data):
                item_str = str(item)
                if len(item_str) > max_display_width:
                    item_str = item_str[:max_display_width-3] + "..."
                result += f"[{i:4d}]  {item_str}\n"
            
            if is_truncated:
                result += f"\n... (showing first {len(data)} of {np.prod(original_shape)} total elements)"
            
            return result
        
        else:
            # Multi-dimensional - show structure and some values
            result = f"Dataset Array ({data.ndim}D):\n" + "-" * 50 + "\n"
            result += f"Shape: {data.shape}\n"
            result += f"Data type: {data.dtype}\n\n"
            
            # Show some flattened values
            flattened = data.flatten()
            result += "Sample values (flattened):\n"
            for i, item in enumerate(flattened[:50]):  # Show first 50
                item_str = str(item)
                if len(item_str) > max_display_width:
                    item_str = item_str[:max_display_width-3] + "..."
                result += f"[{i:4d}]  {item_str}\n"
            
            if len(flattened) > 50:
                result += f"... (showing first 50 of {len(flattened)} total elements)"
            
            return result
    
    @staticmethod
    def format_dataset_info(info: dict) -> str:
        """
        Format dataset information for display
        
        Args:
            info: Dictionary containing dataset information
            
        Returns:
            Formatted string with dataset information
        """
        lines = []
        
        # Basic information
        lines.append(f"Path: {info['path']}")
        lines.append(f"Shape: {info['shape']}")
        lines.append(f"Data Type: {info['dtype']}")
        lines.append(f"Total Elements: {info['size']:,}")
        lines.append(f"Dimensions: {info['ndim']}")
        
        # Optional information
        if info.get('maxshape'):
            lines.append(f"Max Shape: {info['maxshape']}")
        
        if info.get('chunks'):
            lines.append(f"Chunks: {info['chunks']}")
        
        if info.get('compression'):
            lines.append(f"Compression: {info['compression']}")
        
        if info.get('fillvalue') is not None:
            lines.append(f"Fill Value: {info['fillvalue']}")
        
        # Attributes
        if info.get('attributes'):
            lines.append("\nAttributes:")
            for key, value in info['attributes'].items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)