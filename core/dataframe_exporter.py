# core/dataframe_exporter.py
import h5py
import pandas as pd
from typing import List, Optional

class DataFrameExporter:
    def export_to_csv(self, h5_file_path: str, dataset_path: str, columns: List[str], rows: Optional[List[int]], output_csv_path: str) -> None:
        """
        Exports selected columns and rows of an HDF5 dataset/group to a CSV file.

        Args:
            h5_file_path (str): Path to the HDF5 file.
            dataset_path (str): Path to the dataset or group within the HDF5 file.
            columns (List[str]): List of column names to export.
            rows (Optional[List[int]]): List of row indices to export. If None, all rows are exported.
            output_csv_path (str): Path where the CSV file will be saved.
        """
        try:
            # When exporting, it's generally best to let pandas handle the reading
            # of HDFStore formats. For non-HDFStore datasets, h5py direct read works.
            # The read_dataset in H5FileHandler is already designed to handle both.
            from core.h5_file_handler import H5FileHandler
            file_handler = H5FileHandler()

            # Read the full or sliced data into a DataFrame
            # If `rows` are provided, we should ideally pass a slice to read_dataset
            # to avoid loading the entire dataset into memory if only a few rows are needed.
            # However, pandas.read_hdf's `start` and `stop` parameters might not
            # behave exactly like direct integer slicing if `rows` are sparse.
            # For simplicity, if `rows` are sparse, we'll read all necessary data
            # and then filter with pandas. If `rows` imply a continuous slice,
            # we can pass it to read_dataset.

            data_df: pd.DataFrame
            if rows is not None and len(rows) > 0:
                # Check if rows are a continuous slice
                is_continuous_slice = (len(rows) > 0 and
                                       all(rows[i] + 1 == rows[i+1] for i in range(len(rows)-1)))
                if is_continuous_slice:
                    start_row = min(rows)
                    end_row = max(rows) + 1 # pandas slice is exclusive at end
                    data_df = file_handler.read_dataset(h5_file_path, dataset_path, slice_rows=(start_row, end_row))
                else:
                    # If rows are sparse, read the full dataset (or a large chunk) and then filter
                    # For extremely large files, this could still be memory intensive.
                    # A more advanced solution would involve iterating and appending.
                    data_df = file_handler.read_dataset(h5_file_path, dataset_path)
                    # Filter by index
                    data_df = data_df.iloc[rows]
            else:
                # Read all data
                data_df = file_handler.read_dataset(h5_file_path, dataset_path)

            if not isinstance(data_df, pd.DataFrame):
                raise TypeError("Data read from HDF5 file is not a pandas DataFrame. Cannot export.")

            # Filter columns
            # Ensure all requested columns exist in the DataFrame
            existing_columns = [col for col in columns if col in data_df.columns]
            if len(existing_columns) != len(columns):
                missing_cols = set(columns) - set(existing_columns)
                print(f"Warning: The following requested columns were not found in the dataset and will be skipped: {missing_cols}")
            data_df = data_df[existing_columns]

            # Export to CSV
            data_df.to_csv(output_csv_path, index=False)

        except Exception as e:
            raise Exception(f"An error occurred during CSV export: {e}")