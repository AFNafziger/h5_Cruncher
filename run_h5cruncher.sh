#!/bin/bash

echo "Loading Python 3.12.4..."
module load python3/3.12.4

echo "Installing required packages (if not already installed)..."
pip install --user --quiet h5py numpy ttkbootstrap

echo "Launching H5 Cruncher..."
python main.py

