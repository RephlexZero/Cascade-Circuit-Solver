"""
This module manages writing circuit analysis results to CSV files. It supports writing headers and data rows with proper formatting based on magnitude prefixes and dB conversion. Additional utilities create and align CSV files for improved readability.

Functions:
    write_header(circuit, csv_file): Writes header rows with parameter names and units.
    write_data_line(circuit, csv_file): Writes a single data row with calculated values.
    write_empty_csv(output_file_path): Creates an empty CSV file.
    align_and_overwrite_csv(csv_file_path): Aligns columns and overwrites the original CSV file.
"""

import csv
import shutil
from tempfile import NamedTemporaryFile
import numpy as np

# Maps magnitude prefixes to their numerical factors for scaling values appropriately in the CSV.
magnitude_multiplier = {
    '': 1, 'k': 1e3, 'M': 1e6, 'G': 1e9,
    'm': 1e-3, 'u': 1e-6, 'µ': 1e-6, 'n': 1e-9
}

def write_header(circuit, csv_file):
    """
    Writes the header rows for the CSV file. The first row lists the output parameter names,
    and the second row specifies their units, accommodating both dB and linear formats.
    """
    writer = csv.writer(csv_file)
    names = ['Freq']
    units = ['Hz']
    for output in circuit.outputs:
        if output.is_db:
            names += [f'|{output.name}|', f'/_{output.name}']
            units += [f'dB{output.magnitude}{output.unit}', 'Rads']
        else:
            names += [f'Re({output.name})', f'Im({output.name})']
            units += [f'{output.magnitude}{output.unit}']*2
    writer.writerow(names)
    writer.writerow(units)
    csv_file.flush()

def write_data_line(circuit, csv_file):
    """
    Writes a data row with calculated output values at the current frequency, formatted for magnitude and phase,
    handling special cases for power and impedance in dB scale, and ensuring magnitude prefixes are correctly applied.
    """
    writer = csv.writer(csv_file)
    row = ['{:.3e}'.format(circuit.frequency)]
    for output in circuit.outputs:
        output.value /= magnitude_multiplier.get(output.magnitude, 1)
        if output.is_db:
            mag = 10 * np.log10(np.abs(output.value)) if output.name in ['Pin', 'Pout', 'Zin', 'Zout'] else 20 * np.log10(np.abs(output.value))
            phase = np.angle(output.value)
            row += ['{:.3e}'.format(mag), '{:.3e}'.format(phase)]
        else:
            row += ['{:.3e}'.format(np.real(output.value)), '{:.3e}'.format(np.imag(output.value))]
    row.append('')
    writer.writerow(row)
    csv_file.flush()

def write_empty_csv(output_file_path):
    """
    Creates an empty CSV file at the specified path to ensure that the file structure is initialized properly
    or to reset the file in case of errors during data handling.
    """
    with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
        csvfile.close()

def read_and_process_csv(csv_file_path):
    """
    Reads the CSV file and calculates the maximum width for each column to prepare for alignment.
    This helps ensure that the data is visually coherent and easier to analyze.
    """
    rows, max_widths = [], []
    with open(csv_file_path, 'r', newline='', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            rows.append(row)
            if len(max_widths) < len(row):
                max_widths.extend([0] * (len(row) - len(max_widths)))
            for i, cell in enumerate(row):
                max_widths[i] = max(max_widths[i], len(cell.lstrip('-+')))
    return rows, max_widths

def write_aligned_csv(csv_file_path, rows, max_widths):
    """
    Writes aligned data to a temporary file and replaces the original file. This is crucial for maintaining a
    uniform format across the CSV, which facilitates easier data interpretation and analysis.
    """
    with NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf8') as temp_file:
        writer = csv.writer(temp_file)
        for row in rows:
            writer.writerow([cell.rjust(max_widths[i] + 2) for i, cell in enumerate(row)])
    shutil.move(temp_file.name, csv_file_path)

def align_and_overwrite_csv(csv_file_path):
    """
    Aligns columns in a CSV file and overwrites the original file with the aligned version.
    Ensures that the data layout is consistent and aesthetically pleasing for any users of the data.
    """
    rows, max_widths = read_and_process_csv(csv_file_path)
    write_aligned_csv(csv_file_path, rows, max_widths)
