import sys
from net_parser import parse_net_file_to_circuit
from circuit import *
import numpy as np
import matplotlib.pyplot as plt



def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input.net> <output.csv>")
        sys.exit(1)

    # Pull input and output file paths from command line
    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]

    # Check input is .net and output is .csv
    if not input_file_path.endswith('.net') or not output_file_path.endswith('.csv'):
        print("Input file must be a .net file and output file must be a .csv file")
        sys.exit(1)

    Circuit = parse_net_file_to_circuit(input_file_path)
    Circuit.sort_components()

    # Attempt to retrieve linear frequency start and end
    fstart = getattr(Circuit.terminations, 'Fstart', None)
    fend = getattr(Circuit.terminations, 'Fend', None)

    # Attempt to retrieve logarithmic frequency start and end
    Lfstart = getattr(Circuit.terminations, 'LFstart', None)
    Lfend = getattr(Circuit.terminations, 'LFend', None)

    # Attempt to convert nfreqs to int if it exists
    nfreqs = getattr(Circuit.terminations, 'Nfreqs', None)
    if nfreqs is not None:
        nfreqs = int(nfreqs)
    else:
        raise ValueError("Nfreqs is not defined.")
    print(fstart, fend, Lfstart, Lfend, nfreqs)
    # Check conditions and decide which function to call
    if all([fstart, fend, nfreqs]) and all(x > 0 for x in [fstart, fend, nfreqs]):
        # Linear frequency variables are available and valid
        frequencies = np.linspace(fstart, fend, nfreqs)
    elif all([Lfstart, Lfend, nfreqs]) and all(x > 0 for x in [Lfstart, Lfend, nfreqs]):
        # Logarithmic frequency variables are available and valid
        frequencies = np.logspace(np.log10(Lfstart), np.log10(Lfend), nfreqs)
    else:
        # Handle cases where the necessary variables are not available or are invalid
        raise ValueError("Required variables for either linear or logarithmic frequency steps are not properly defined.")
  
    results = []
    for f in frequencies:
        Circuit.solve(f)
        
    for result in results:
        print(result.frequency)
if __name__ == "__main__":
    main()