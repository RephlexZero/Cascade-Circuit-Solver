import sys
from net_parser import parse_net_file_to_circuit
from circuit import *
from circuit_matricies import *
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
    Circuit.components = sorted(Circuit.components, key=lambda x: (x.n1, x.n2))
    transition_matricies = [get_abcd_matrix(component) for component in Circuit.components]
    print(multiply_matrices(transition_matricies))
if __name__ == "__main__":
    main()

# TODO: Cascade analysis: group by node ingress, shunt, and egress