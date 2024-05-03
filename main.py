"""
This module is the main entry point of the circuit analysis program. 

It parses the input .net file, analyzes the circuit at specified frequencies, 
and writes the results to a CSV file with aligned columns. 

Functions:
    main():
        Parses input file, analyzes the circuit, and writes results to a CSV file.
"""
import cProfile
import sys
from csv_writer import write_empty_csv
from net_parser import parse_net_file_to_circuit

def main(input_file_path, output_file_path):
    """
    This function serves as the entry point of the program. It performs the following tasks:

    1. Parses the input .net file using the `parse_net_file_to_circuit` function.
    2. Handles any errors that occur during parsing.
    3. Sorts the components in the circuit for consistent matrix multiplication order.
    4. Determines the frequency range and number of frequencies for analysis.
    5. Solves the circuit for each frequency and writes the results to a CSV file. 
    6. Aligns the columns in the CSV file for better readability.
    """
    circuit = parse_net_file_to_circuit(input_file_path)
    circuit.solve(output_file_path)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 2:
        raise ValueError("Invalid number of arguments")
    # Get the input and output file paths from command line arguments.
    input_file_path, output_file_path = args[0], args[1]
    # Check input file is .net and output file is .csv
    if not input_file_path.endswith('.net') or not output_file_path.endswith('.csv'):
        raise ValueError("Input file must be a .net file and output file must be a .csv file.")
    try:
        # cProfile.run('main(input_file_path, output_file_path)', f'{input_file_path.replace(".net",".prof")}') # Uncomment to profile the code
        main(input_file_path, output_file_path)
    # In all exceptions, create an empty CSV file to indicate an error occurred.
    except Exception as e:
        print(f"An error occurred: {e}")
        with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
            write_empty_csv(csvfile)
        sys.exit(1)