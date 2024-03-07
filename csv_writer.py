import csv
import numpy as np

magnitude_multiplier = {
    '': 1, 'k': 1e3,
    'M': 1e6, 'G': 1e9,
    'm': 1e-3, 'u': 1e-6,
    'µ': 1e-6, 'n': 1e-9
}


def write_header(Circuit, csv_file):
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
            names.append(f'Re({output.name})')
            names.append(f'Im({output.name})')
            for _ in range(2):
                units.append(f'{output.magnitude}{output.unit}')
    writer.writerow(names)
    writer.writerow(units)
    csv_file.flush()


def write_data(frequencies, results, csv_file):
    writer = csv.writer(csv_file)

    for i, f in enumerate(frequencies):
        row = ['{:.3e}'.format(f)]
        for output in results[i]:  # Assuming 'outputs' is a key in the dict
            output.value = output.value / magnitude_multiplier.get(output.magnitude, 1)
            # Convert the value to scientific notation (3dp)
            if output.is_db:
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
    with open(output_file_path, 'w', newline='') as csvfile:  # Open in write mode ('w')
        csvfile.close()


from tempfile import NamedTemporaryFile
import shutil


def align_and_overwrite_csv(csv_file_path):
    """
    Reads a CSV file, aligns its contents for better readability, and overwrites
    the original file with the aligned content.

    Args:
    - csv_file_path (str): The path to the CSV file to be read, aligned, and overwritten.
    """
    # Determine the maximum width of each column
    max_widths = []
    with open(csv_file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(max_widths) < len(row):
                max_widths.extend([0] * (len(row) - len(max_widths)))
            for i, cell in enumerate(row):
                # Strip +/- characters from the cell before checking its length
                stripped_cell = cell.lstrip('-+')
                max_widths[i] = max(max_widths[i], len(stripped_cell))

    # Use a temporary file to write the aligned content
    temp_file = NamedTemporaryFile(mode='w', delete=False, newline='')
    with open(csv_file_path, 'r', newline='') as csvfile, temp_file:
        reader = csv.reader(csvfile)
        writer = csv.writer(temp_file)
        for row in reader:
            # Align each cell and write the row to the temp file
            aligned_row = [cell.rjust(max_widths[i] + 2) for i, cell in enumerate(row)]
            # Only pad the first column by one space
            aligned_row[0] = aligned_row[0][1:]
            writer.writerow(aligned_row)

    # Replace the original file with the temp file
    shutil.move(temp_file.name, csv_file_path)
