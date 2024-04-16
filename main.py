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
    try:
        # Parse the circuit definition from the input .net file.
        circuit = parse_net_file_to_circuit(input_file_path)
    except MalformedInputError as e:
        # If there's an error during parsing, create an empty CSV file and print an error message.
        write_empty_csv(output_file_path)
        print(f"Error parsing input file: {e}")
        sys.exit(1)  # Exit the program with an error code.

    # Sort the components in the circuit to ensure correct order for ABCD matrix calculations.
    circuit.sort_components() 
    # Print the sorted component information (for debugging/verification).
    for component in circuit.components:
        print(f"n1={component.n1} n2={component.n2} {component.type}={component.value}")

    # Try to retrieve linear frequency sweep parameters (start and end frequencies, number of points).
    fstart = getattr(circuit.terminations, 'Fstart', None) 
    fend = getattr(circuit.terminations, 'Fend', None)
    nfreqs = getattr(circuit.terminations, 'Nfreqs', None)

    # If linear sweep parameters are not available, try to get logarithmic sweep parameters.
    if not all([fstart, fend, nfreqs]):
        lfstart = getattr(circuit.terminations, 'LFstart', None)
        lfend = getattr(circuit.terminations, 'LFend', None)
        nfreqs = getattr(circuit.terminations, 'Nfreqs', None)  # Number of frequencies remains the same. 

    # Check if the necessary frequency parameters are valid and generate the frequency range. 
    if all([fstart, fend, nfreqs]) and all(x > 0 for x in [fstart, fend, nfreqs]):
        # Create a linearly spaced array of frequencies.
        frequencies = np.linspace(fstart, fend, int(nfreqs))  
    elif all([lfstart, lfend, nfreqs]) and all(x > 0 for x in [lfstart, lfend, nfreqs]):
        # Create a logarithmically spaced array of frequencies.
        frequencies = np.logspace(np.log10(lfstart), np.log10(lfend), int(nfreqs)) 
    else:
        # If frequency parameters are invalid or missing, create an empty CSV and raise an error.
        write_empty_csv(output_file_path)
        raise ValueError("Invalid or missing frequency parameters")

    # Open the output CSV file in write mode.
    with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
        # Write the header rows with parameter names and units.
        write_header(circuit, csvfile)  
        for f in frequencies:
            try:
                # Solve the circuit at the current frequency and get the output values.
                circuit.solve(f)  
                # Write the calculated values to a row in the CSV file.
                write_data_line(circuit, csvfile)  
            except ValueError as e:
                # If there's an error during circuit analysis, create an empty CSV and print an error message. 
                csvfile.close()
                write_empty_csv(output_file_path)
                print(f"Error solving circuit: {e} at frequency {f} Hz")
                sys.exit(1)
        csvfile.close()
    
    # Align the columns in the CSV file for better readability.
    align_and_overwrite_csv(output_file_path)  


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <input.net> <output.csv>")
        raise SystemExit(1)

    # Get the input and output file paths from command line arguments.
    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]

    # Check if the input file has a .net extension and the output file has a .csv extension.
    if not input_file_path.endswith('.net') or not output_file_path.endswith('.csv'):
        print("Input file must be a .net file and output file must be a .csv file")
        sys.exit(1)

    # Run the main function to start the circuit analysis process.
    main()