import csv
import numpy as np

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
    magnitude_multipliers = {
        '': 1,   # Base case, no magnitude prefix
        'k': 1e3, 'M': 1e6, 'G': 1e9, 
        'm': 1e-3, 'u': 1e-6, 'n': 1e-9
    }
    
    writer = csv.writer(csv_file)

    for i, f in enumerate(frequencies):
        row = ['{:.3e}'.format(f)]
        for output in results[i]:  # Assuming 'outputs' is a key in the dict
            output.value = output.value / magnitude_multipliers.get(output.magnitude, 1)
            # Convert the value to scientific notation (3dp)
            if output.is_db:
                mag, phase = (20 * np.log10(np.abs(output.value))), (np.angle(output.value))
                row.append('{:.3e}'.format(mag))  # Format using 'E' for scientific notation
                row.append('{:.3e}'.format(phase))
            else:
                value = output.value  # Extract the value
                row.append('{:.3e}'.format(np.real(value)))  # Format using 'E' for scientific notation
                row.append('{:.3e}'.format(np.imag(value)))

        writer.writerow(row)
    csv_file.flush() 
