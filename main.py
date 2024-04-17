"""
This module is the main entry point of the circuit analysis program. 

It parses the input .net file, analyzes the circuit at specified frequencies, 
and writes the results to a CSV file with aligned columns. 

Functions:
    main():
        Parses input file, analyzes the circuit, and writes results to a CSV file.
"""
import sys
import numpy as np

from csv_writer import write_header, write_data_line, write_empty_csv, align_and_overwrite_csv
from net_parser import parse_net_file_to_circuit, MalformedInputError


def main():
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

    # Sort the components in the circuit to ensure correct order for ABCD matrix calculations.
    circuit.sort_components()
    # Print the sorted component information (for debugging/verification).
    # for component in circuit.components:
    #     print(f"n1={component.n1} n2={component.n2} {component.type}={component.value}")

    # Try to retrieve linear frequency sweep parameters (start and end frequencies, number of points).
    def calculate_frequencies(circuit, linear_keys, log_keys):
        # Retrieve parameters for linear or logarithmic frequency sweep
        params = {key: getattr(circuit.terminations, key, None) for key in linear_keys + log_keys}
        
        # Attempt to use linear sweep parameters first
        if all(params[key] is not None and params[key] > 0 for key in linear_keys):
            fstart, fend, nfreqs = (params[key] for key in linear_keys)
            return np.linspace(fstart, fend, int(nfreqs))
        
        # If linear parameters are not valid, try logarithmic
        if all(params[key] is not None and params[key] > 0 for key in log_keys):
            lfstart, lfend, nfreqs = (params[key] for key in log_keys)
            return np.logspace(np.log10(lfstart), np.log10(lfend), int(nfreqs))
        
        # If neither set is valid, raise an error
        missing_params = [key for key in linear_keys + log_keys if params[key] is None or params[key] <= 0]
        raise ValueError(f"Invalid or missing frequency parameters: {', '.join(missing_params)}")

    # Keys for linear and logarithmic frequency parameters
    linear_keys = ['Fstart', 'Fend', 'Nfreqs']
    log_keys = ['LFstart', 'LFend', 'Nfreqs']
    
    frequencies = calculate_frequencies(circuit, linear_keys, log_keys)

    # Open the output CSV file in write mode.
    with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
        # Write the header rows with parameter names and units.
        write_header(circuit, csvfile)
        for f in frequencies:
            # Solve the circuit at the current frequency and get the output values.
            circuit.solve(f)
            # Write the calculated values to a row in the CSV file.
            write_data_line(circuit, csvfile)
        csvfile.close()
    # Align the columns in the CSV file for better readability.
    align_and_overwrite_csv(output_file_path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <input.net> <output.csv>")
        raise ValueError("Invalid command arguments")

    # Get the input and output file paths from command line arguments.
    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]

    # Check if the input file has a .net extension and the output file has a .csv extension.
    if not input_file_path.endswith('.net') or not output_file_path.endswith('.csv'):
        print("Input file must be a .net file and output file must be a .csv file")
        raise ValueError("Invalid file argument extension(s)")

    # Run the main function to start the circuit analysis process.
    try:
        main()
    # In all exceptions, create an empty CSV file to indicate an error occurred.
    except Exception as e:
        print(f"An error occurred: {e}")
        write_empty_csv(output_file_path)
