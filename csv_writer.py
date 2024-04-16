"""
This module handles writing circuit analysis results to CSV files.

The `write_header` function writes the header rows to the CSV file, including 
parameter names and units.

The `write_data_line` function writes a single data row to the CSV file containing 
the calculated values for the output parameters at the current frequency, with 
proper formatting based on magnitude prefixes and dB conversion.

Additional functions handle creating an empty CSV file and aligning columns for 
better readability.

Functions:
    write_header(circuit, csv_file):
        Writes the header rows with parameter names and units. 
    write_data_line(circuit, csv_file):
        Writes a single data row with calculated values.
    write_empty_csv(output_file_path):
        Creates an empty CSV file at the specified path.
    align_and_overwrite_csv(csv_file_path):
        Aligns columns and overwrites the original CSV file.

Helper Functions:
    read_and_process_csv(csv_file_path): 
        Reads the CSV file and determines column widths for alignment.
    write_aligned_csv(csv_file_path, rows, max_widths):
        Writes aligned data to a temporary file and replaces the original.
"""

import csv
import shutil
from tempfile import NamedTemporaryFile
import numpy as np

# A dictionary that maps magnitude prefixes to their corresponding numerical factors.
# This is used when writing data to the CSV file to ensure that values are
# expressed with the appropriate scaling based on their units.
magnitude_multiplier = {
    '': 1, 'k': 1e3,
    'M': 1e6, 'G': 1e9,
    'm': 1e-3, 'u': 1e-6,
    'µ': 1e-6, 'n': 1e-9
}


def write_header(circuit, csv_file):
    """
    Writes the header rows to the CSV file. The first row contains the names
    of the output parameters, and the second row specifies their units.

    Args:
        circuit: The Circuit object containing information about the output parameters.
        csv_file: The open file object representing the CSV file where the header will be written.
    """
    writer = csv.writer(csv_file)  # Create a CSV writer object for writing rows to the file.

    # Initialize lists to store parameter names and units. 
    names = ['Freq']  # Start with 'Freq' for frequency
    units = ['Hz']   # Units for frequency is 'Hz'

    # Iterate over each output parameter in the circuit.
    for output in circuit.outputs:
        if output.is_db:
            # For dB outputs, add two columns: one for magnitude (|parameter|) and one for phase (/_parameter).
            names.append(f'|{output.name}|')
            names.append(f'/_{output.name}')

            # Specify units as dB with the corresponding magnitude prefix and unit (e.g., dBmV, dBuA).
            units.append(f'dB{output.magnitude}{output.unit}')
            units.append('Rads')  # Phase is expressed in radians.
        else:
            # For linear outputs, add two columns: one for the real part (Re(parameter)) and one for the imaginary part (Im(parameter)).
            if output.name in ['Av', 'Ai', 'Ap']:  # Special case for gain parameters (unitless)
                output.unit = 'L'
            names.append(f'Re({output.name})')
            names.append(f'Im({output.name})')

            # Specify units with the corresponding magnitude prefix and unit (e.g., mV, uA).
            for _ in range(2):
                units.append(f'{output.magnitude}{output.unit}')

    # Write the parameter names and units as two separate rows in the CSV file.
    writer.writerow(names)
    writer.writerow(units)
    csv_file.flush()  # Ensure the data is written to the file.


def write_data_line(circuit, csv_file):
    """
    Writes a single data row to the CSV file, containing the calculated values for 
    the output parameters at the current frequency. Handles formatting based 
    on magnitude prefixes and dB conversion as needed.

    Args:
        circuit: The Circuit object with the calculated output values.
        csv_file: The open file object representing the CSV file where the data row will be written.
    """
    writer = csv.writer(csv_file)  # Create a CSV writer object.

    # Start the row with the frequency value in scientific notation with 3 decimal places.
    row = ['{:.3e}'.format(circuit.frequency)]  

    # Iterate over each output parameter in the circuit.
    for output in circuit.outputs:
        # Adjust the value based on the magnitude prefix.
        output.value = output.value / magnitude_multiplier.get(output.magnitude, 1)

        if output.is_db:  # Handle dB output.
            if output.name in ['Pin', 'Pout', 'Zin', 'Zout']:  # Special cases for power and impedance
                mag = 10 * np.log10(np.abs(output.value))  # Calculate magnitude in dB.
            else:
                mag = 20 * np.log10(np.abs(output.value))  # Calculate magnitude in dB (general case).
            phase = np.angle(output.value)  # Calculate phase in radians.

            # Append magnitude and phase to the row in scientific notation with 3 decimal places.
            row.append('{:.3e}'.format(mag))  
            row.append('{:.3e}'.format(phase))  
        else:  # Handle linear output.
            value = output.value  # Extract the complex value.
            # Append the real and imaginary parts to the row in scientific notation with 3 decimal places.
            row.append('{:.3e}'.format(np.real(value)))  
            row.append('{:.3e}'.format(np.imag(value)))

    # Add an empty element at the end of the row to ensure consistent formatting with commas.
    row.append('') 
    writer.writerow(row)  # Write the row to the CSV file.
    csv_file.flush()  # Ensure the data is written to the file.


def write_empty_csv(output_file_path):
    """
    Creates an empty CSV file at the specified path. This is used in case of errors
    during the parsing or analysis process. 

    Args:
        output_file_path: The path where the empty CSV file will be created.
    """
    with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
        csvfile.close()


def read_and_process_csv(csv_file_path):
    """
    Reads the CSV file and determines the maximum width for each column to prepare
    for alignment.

    Args:
        csv_file_path: The path to the CSV file.

    Returns:
        A tuple containing:
            - rows: A list of lists representing the rows of the CSV file.
            - max_widths: A list containing the maximum width of each column. 
    """
    rows = []
    max_widths = []
    with open(csv_file_path, 'r', newline='', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            rows.append(row)
            if len(max_widths) < len(row):
                max_widths.extend([0] * (len(row) - len(max_widths)))
            for i, cell in enumerate(row):
                stripped_cell = cell.lstrip('-+')  # Ignore leading signs for width calculation.
                max_widths[i] = max(max_widths[i], len(stripped_cell))
    return rows, max_widths


def write_aligned_csv(csv_file_path, rows, max_widths):
    """
    Writes the data to a new temporary CSV file with aligned columns and then 
    replaces the original file.

    Args:
        csv_file_path: The path to the original CSV file.
        rows: A list of lists representing the rows of the CSV file.
        max_widths: A list containing the maximum width of each column.
    """
    with NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf8') as temp_file:
        writer = csv.writer(temp_file)
        for row in rows:
            aligned_row = [cell.rjust(max_widths[i] + 2) for i, cell in enumerate(row)]
            aligned_row[0] = aligned_row[0][1:]  # Remove extra space before the first element.
            aligned_row[-1] = aligned_row[-1].rstrip()  # Remove trailing space from the last element.
            writer.writerow(aligned_row)
    shutil.move(temp_file.name, csv_file_path)  # Replace the original file with the aligned version.


def align_and_overwrite_csv(csv_file_path):
    """
    Aligns the columns of a CSV file and overwrites the original file with the
    aligned content. 

    Args:
        csv_file_path: The path to the CSV file to be aligned.
    """
    try:
        rows, max_widths = read_and_process_csv(csv_file_path)
        write_aligned_csv(csv_file_path, rows, max_widths)
    except (FileNotFoundError, PermissionError) as e:
        print(f"An error occurred: {e}") 