import sys
from net_parser import parse_net_file_to_circuit, MalformedInputError
from circuit import Circuit
import numpy as np
import copy
from csv_writer import write_header, write_data, write_empty_csv

def main():
    try:
        Circuit = parse_net_file_to_circuit(input_file_path)
    except MalformedInputError as e:
        write_empty_csv(output_file_path)
        print(f"Error parsing input file: {e}")
        sys.exit(1)
    
    Circuit.sort_components()

    # Attempt to retrieve linear frequency start and end
    fstart = getattr(Circuit.terminations, 'Fstart', None)
    fend = getattr(Circuit.terminations, 'Fend', None)

    # Attempt to retrieve logarithmic frequency start and end
    Lfstart = getattr(Circuit.terminations, 'LFstart', None)
    Lfend = getattr(Circuit.terminations, 'LFend', None)

    # Attempt to convert nfreqs to int if it exists
    nfreqs = getattr(Circuit.terminations, 'Nfreqs', None)

    # Check conditions and decide which function to call
    if all([fstart, fend, nfreqs]) and all(x > 0 for x in [fstart, fend, nfreqs]):
        # Linear frequency variables are available and valid
        frequencies = np.linspace(fstart, fend, int(nfreqs))
    elif all([Lfstart, Lfend, nfreqs]) and all(x > 0 for x in [Lfstart, Lfend, nfreqs]):
        # Logarithmic frequency variables are available and valid
        frequencies = np.logspace(np.log10(Lfstart), np.log10(Lfend), int(nfreqs))
    else:
        write_empty_csv(output_file_path)
        raise ValueError("Invalid or missing frequency parameters")
        # Handle cases where the necessary variables are not available or are invalid

    results = []
    for i, f in enumerate(frequencies):
        try:
            results.append(copy.deepcopy(Circuit.solve(f)))
        except ValueError as e:
            write_empty_csv(output_file_path)
            print(f"Error solving circuit: {e} at frequency {f} Hz")
            sys.exit(1)
            
    with open(output_file_path, 'w', newline='') as csvfile:  # Open in write mode ('w')
        write_header(Circuit, csvfile)  # Pass the open file object
        write_data(frequencies, results, csvfile)
        csvfile.close()

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