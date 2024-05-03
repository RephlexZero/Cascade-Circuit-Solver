"""
This module manages writing circuit analysis results to CSV files. It supports writing headers and data rows with proper formatting based on magnitude prefixes and dB conversion. Additional utilities create and align CSV files for improved readability.

Functions:
    write_header(circuit, csv_file): Writes header rows with parameter names and units.
    write_data_line(circuit, csv_file): Writes a single data row with calculated values.
    write_empty_csv(output_file_path): Creates an empty CSV file.
    align_and_overwrite_csv(csv_file_path): Aligns columns and overwrites the original CSV file.
"""

import csv
import numpy as np

# Maps magnitude prefixes to their numerical factors for scaling values appropriately in the CSV.
magnitude_multiplier = {
    '': 1, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12, 'P': 1e15,
    'm': 1e-3, 'u': 1e-6, 'µ': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15
}

def write_header(circuit, csv_file):
    """
    Writes the header rows for the CSV file. The first row lists the output parameter names,
    and the second row specifies their units, accommodating both dB and linear formats.
    """
    writer = csv.writer(csv_file)  # Create a CSV writer object for writing rows to the file.

    # Initialize lists to store parameter names and units with consistent formatting
    names = [f'{"Freq":>10}']
    units = [f'{"Hz":>10}']  # Units for frequency is 'Hz'

    # Iterate over each output parameter in the circuit.
    for output in circuit.outputs:
        if output.is_db:
            # For dB outputs, add two columns: one for magnitude and one for phase.
            names.extend([f'{f"|{output.name}|":>11}', f'{f"/_{output.name}":>11}'])
            units.extend([f'{f"dB{output.magnitude}{output.unit}":>11}', f'{"Rads":>11}'])
        else:
            # For linear outputs, add two columns: one for the real part and one for the imaginary part.
            if output.name in ['Av', 'Ai', 'Ap']:  # Special case for gain parameters (unitless)
                output.unit = 'L'
            names.extend([f'{f"Re({output.name})":>11}', f'{f"Im({output.name})":>11}'])
            units.extend([f'{f"{output.magnitude}{output.unit}":>11}' for _ in range(2)])

    # Write header rows to the CSV
    writer.writerow(names)
    writer.writerow(units)

def write_data_line(circuit, csv_file, frequency):
    """
    Writes a data row with calculated output values at the current frequency, formatted for magnitude and phase,
    handling special cases for power and impedance in dB scale, and ensuring magnitude prefixes are correctly applied.
    """
    writer = csv.writer(csv_file)
    row = [f'{frequency:>10.3e}']
    for output in circuit.outputs:
        if output.is_db:
            mag = np.log10(np.absolute(output.value) / magnitude_multiplier.get(output.magnitude, 1))
            if output.name in ['Pin', 'Pout', 'Ap']:
                mag *= 10
                mag = max(mag, -100)
            else:
                mag *= 20
                mag = max(mag, -160)
            phase = np.angle(output.value)
            row.extend([f'{mag:>11.3e}', f'{phase:>11.3e}'])
        else:
            output.value /= magnitude_multiplier.get(output.magnitude, 1)
            row.extend([f'{output.value.real:>11.3e}', f'{output.value.imag:>11.3e}'])
    row.append('')
    writer.writerow(row)

def write_empty_csv(csvfile):
    """
    Writes an empty CSV file.
    """
    csvfile.write('')
