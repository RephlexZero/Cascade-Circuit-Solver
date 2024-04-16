import csv
import numpy as np
import shutil
from tempfile import NamedTemporaryFile

magnitude_multiplier = {
    '': 1, 'k': 1e3,
    'M': 1e6, 'G': 1e9,
    'm': 1e-3, 'u': 1e-6,
    'µ': 1e-6, 'n': 1e-9
}


def write_header(Circuit, csv_file):
    """
    Writes the header row with parameter names and units to the CSV file.

    Args:
        Circuit: A Circuit object containing the output information.
        csv_file: The open file object for the CSV file.
    """
    writer = csv.writer(csv_file)

    names = ['Freq']
    units = ['Hz']
    for output in Circuit.outputs:
        if output.is_db:
            names.append(f'|{output.name}|')
            names.append(f'/_{output.name}')

            units.append(f'dB{output.magnitude}{output.unit}')
            units.append('Rads')
        else:
            if output.name in ['Av', 'Ai', 'Ap']:
                output.unit = 'L'
            names.append(f'Re({output.name})')
            names.append(f'Im({output.name})')
            for _ in range(2):
                units.append(f'{output.magnitude}{output.unit}')
    writer.writerow(names)
    writer.writerow(units)
    csv_file.flush()


def write_data_line(circuit, csv_file):
    """
    Writes a single data row with calculated values to the CSV file, considering magnitude prefixes and dB conversion.

    Args:
        circuit: The Circuit object with the calculated output values.
        csv_file: The open file object for the CSV file.
    """
    writer = csv.writer(csv_file)
    row = ['{:.3e}'.format(circuit.frequency)]
    for output in circuit.outputs:  # Assuming 'outputs' is a key in the dict
        output.value = output.value / magnitude_multiplier.get(output.magnitude, 1)
        # Convert the value to scientific notation (3dp)
        if output.is_db:
            if output.name in ['Pin','Pout','Zin','Zout']:
                mag = 10 * np.log10(np.abs(output.value))
            else:
                mag = 20 * np.log10(np.abs(output.value))
            phase = np.angle(output.value)
            row.append('{:.3e}'.format(mag))  # Format using 'E' for scientific notation
            row.append('{:.3e}'.format(phase))
        else:
            value = output.value  # Extract the value
            row.append('{:.3e}'.format(np.real(value)))  # Format using 'E' for scientific notation
            row.append('{:.3e}'.format(np.imag(value)))
    row.append('')
    writer.writerow(row)
    csv_file.flush()


def write_empty_csv(output_file_path):
    """
    Creates an empty CSV file at the specified path.

    Args:
        output_file_path: The path to create the empty CSV file.
    """
    with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:  # Open in write mode ('w')
        csvfile.close()

def read_and_process_csv(csv_file_path):
    """
    Reads the CSV file and determines the maximum width for each column for alignment purposes.

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
                stripped_cell = cell.lstrip('-+')
                max_widths[i] = max(max_widths[i], len(stripped_cell))
    return rows, max_widths

def write_aligned_csv(csv_file_path, rows, max_widths):
    """
    Writes the data to a new temporary CSV file with aligned columns and then replaces the original file.

    Args:
        csv_file_path: The path to the original CSV file.
        rows: A list of lists representing the rows of the CSV file.
        max_widths: A list containing the maximum width of each column.
    """
    with NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf8') as temp_file:
        writer = csv.writer(temp_file)
        for row in rows:
            aligned_row = [cell.rjust(max_widths[i] + 2) for i, cell in enumerate(row)]
            aligned_row[0] = aligned_row[0][1:]
            aligned_row[-1] = aligned_row[-1].rstrip()
            writer.writerow(aligned_row)
    shutil.move(temp_file.name, csv_file_path)

def align_and_overwrite_csv(csv_file_path):
    """
    Aligns the columns of a CSV file and overwrites the original file with the aligned content.

    Args:
        csv_file_path: The path to the CSV file to be aligned.
    """
    try:
        rows, max_widths = read_and_process_csv(csv_file_path)
        write_aligned_csv(csv_file_path, rows, max_widths)
    except (FileNotFoundError, PermissionError) as e:
        print(f"An error occurred: {e}")