import sys
from net_parser import parse_net_file_to_circuit
from circuit import *
import numpy as np


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
    Circuit.resolve_matrix()
    print(Circuit.T)
    
if __name__ == "__main__":
    main()