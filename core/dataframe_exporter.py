# core/dataframe_exporter.py
import h5py
import pandas as pd
import numpy as np
from typing import List, Optional, Callable

# Modified export_to_csv method with print statements for terminal updates
# Chunk size defaulted to 100000 rows

class DataFrameExporter:
    def export_to_csv(self, h5_file_path: str, dataset_path: str, columns: List[str], 
                     rows: Optional[List[int]], output_csv_path: str, 
                     progress_callback: Optional[Callable[[float, str], None]] = None,
                     chunk_size: int = 100000) -> None:
        try:
            def update_progress(pct, msg):
                print(f"[Progress {pct:.1f}%] {msg}")
                if progress_callback:
                    progress_callback(pct, msg)

            update_progress(5, "Initializing chunked export...")

            from core.h5_file_handler import H5FileHandler
            file_handler = H5FileHandler()

            update_progress(10, "Analyzing dataset structure...")
            info = file_handler.get_dataset_info(h5_file_path, dataset_path)

            if rows:
                row_indices = sorted(rows)
                total_rows_to_export = len(row_indices)
                is_continuous_slice = (len(row_indices) > 1 and all(row_indices[i] + 1 == row_indices[i+1] for i in range(len(row_indices)-1)))
            else:
                if isinstance(info['shape'], tuple) and len(info['shape']) > 0:
                    total_dataset_rows = info['shape'][0]
                else:
                    sample_data, _ = file_handler.get_dataset_data(h5_file_path, dataset_path, max_elements=1)
                    total_dataset_rows = len(sample_data) if isinstance(sample_data, pd.DataFrame) else file_handler.read_dataset(h5_file_path, dataset_path).shape[0]

                row_indices = list(range(total_dataset_rows))
                total_rows_to_export = total_dataset_rows
                is_continuous_slice = True

            update_progress(15, f"Preparing to export {total_rows_to_export:,} rows in chunks...")

            update_progress(20, "Validating column selection...")
            sample_data, _ = file_handler.get_dataset_data(h5_file_path, dataset_path, max_elements=100)
            if isinstance(sample_data, pd.DataFrame):
                available_columns = list(sample_data.columns)
                existing_columns = [col for col in columns if col in available_columns]
                missing_cols = set(columns) - set(existing_columns)
                if missing_cols:
                    print(f"Warning: Missing columns skipped: {missing_cols}")
                columns = existing_columns
            if not columns:
                raise ValueError("No valid columns for export")

            chunks = []
            if is_continuous_slice and not rows:
                chunks = [(i, min(i + chunk_size, total_rows_to_export)) for i in range(0, total_rows_to_export, chunk_size)]
            else:
                for i in range(0, len(row_indices), chunk_size):
                    chunks.append(row_indices[i:i + chunk_size])

            update_progress(25, f"Beginning chunked export: {len(chunks)} chunks of up to {chunk_size:,} rows")

            for chunk_idx, chunk in enumerate(chunks):
                update_progress(25 + (chunk_idx / len(chunks)) * 70, f"Processing chunk {chunk_idx+1}/{len(chunks)}")

                if is_continuous_slice and not rows:
                    start, end = chunk
                    df = file_handler.read_dataset(h5_file_path, dataset_path, slice_rows=(start, end))
                else:
                    start, end = min(chunk), max(chunk)
                    df = file_handler.read_dataset(h5_file_path, dataset_path, slice_rows=(start, end+1))
                    if isinstance(df, pd.DataFrame):
                        df = df.iloc[[i - start for i in chunk]]

                df = df[columns]
                df.to_csv(output_csv_path, mode='w' if chunk_idx == 0 else 'a', header=(chunk_idx == 0), index=False)

                rows_done = min((chunk_idx + 1) * chunk_size, total_rows_to_export)
                print(f"Wrote chunk {chunk_idx+1}/{len(chunks)} ({rows_done:,}/{total_rows_to_export:,} rows)")

            update_progress(95, "Finalizing export...")
            import os
            if os.path.exists(output_csv_path) and os.path.getsize(output_csv_path) > 0:
                update_progress(100, f"Export complete: {output_csv_path} ({total_rows_to_export:,} rows)")
            else:
                raise Exception("Export file is empty or missing")

        except InterruptedError:
            # Re-raise cancellation errors without modification
            if progress_callback:
                progress_callback(0, "Export cancelled by user")
            raise
        except Exception as e:
            error_msg = f"Chunked export failed: {str(e)}"
            if progress_callback:
                progress_callback(0, error_msg)
            raise Exception(error_msg)