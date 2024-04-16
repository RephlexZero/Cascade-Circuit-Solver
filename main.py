import csv
import sys
import copy
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from csv_writer import write_header, write_data_line, write_empty_csv, align_and_overwrite_csv
from net_parser import parse_net_file_to_circuit, MalformedInputError


def main():
    try:
        circuit = parse_net_file_to_circuit(input_file_path)
    except MalformedInputError as e:
        write_empty_csv(output_file_path)
        print(f"Error parsing input file: {e}")
        sys.exit(1)

    circuit.sort_components()
    for component in circuit.components:
        print(f"n1={component.n1} n2={component.n2} {component.type}={component.value}")
    # Attempt to retrieve linear frequency start and end
    fstart = getattr(circuit.terminations, 'Fstart', None)
    fend = getattr(circuit.terminations, 'Fend', None)

    # Attempt to retrieve logarithmic frequency start and end
    lfstart = getattr(circuit.terminations, 'LFstart', None)
    lfend = getattr(circuit.terminations, 'LFend', None)

    # Attempt to convert nfreqs to int if it exists
    nfreqs = getattr(circuit.terminations, 'Nfreqs', None)

    # Check conditions and decide which function to call
    if all([fstart, fend, nfreqs]) and all(x > 0 for x in [fstart, fend, nfreqs]):
        # Linear frequency variables are available and valid
        frequencies = np.linspace(fstart, fend, int(nfreqs))
    elif all([lfstart, lfend, nfreqs]) and all(x > 0 for x in [lfstart, lfend, nfreqs]):
        # Logarithmic frequency variables are available and valid
        frequencies = np.logspace(np.log10(lfstart), np.log10(lfend), int(nfreqs))
    else:
        write_empty_csv(output_file_path)
        raise ValueError("Invalid or missing frequency parameters")
        # Handle cases where the necessary variables are not available or are invalid

    with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
        write_header(circuit, csvfile)  # Pass the open file object
        for f in frequencies:
            try:
                circuit.solve(f)
                write_data_line(circuit, csvfile)
            except ValueError as e:
                csvfile.close()
                write_empty_csv(output_file_path)
                print(f"Error solving circuit: {e} at frequency {f} Hz")
                sys.exit(1)
        csvfile.close()
    align_and_overwrite_csv(output_file_path)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <input.net> <output.csv>")
        raise SystemExit(1)

    # Pull input and output file paths from command line
    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]

    # Check input is .net and output is .csv
    if not input_file_path.endswith('.net') or not output_file_path.endswith('.csv'):
        print("Input file must be a .net file and output file must be a .csv file")
        sys.exit(1)
    main()
