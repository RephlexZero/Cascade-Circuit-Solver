"""
This module is responsible for parsing .net files, which contain circuit definitions, 
and converting them into Circuit objects for analysis.

The `parse_net_file_to_circuit` function reads the .net file, extracts circuit components,
terminations, and output specifications, and creates a Circuit object to represent 
the circuit internally.

Classes:
    MalformedInputError: Custom exception for invalid .net file formats.

Functions:
    parse_net_file_to_circuit(file_path): 
        Parses a .net file and returns a Circuit object.

Helper Functions:
    process_circuit_line(line, circuit):
        Processes a line from the CIRCUIT section and adds a component to the circuit.
    process_terms_line(line, circuit):
        Processes a line from the TERMS section and sets termination parameters.
    process_output_line(line, circuit):
        Processes a line from the OUTPUT section and adds an output parameter.
"""
import re
from circuit import Circuit


class MalformedInputError(Exception):
    """
    This custom exception is used to indicate that the input .net file
    does not adhere to the expected format. It helps identify and handle
    errors during the parsing process.
    """


# A dictionary that maps magnitude prefixes to their corresponding numerical factors.
# This is used to convert component values and termination parameters from their
# string representations to numerical values with appropriate scaling.
magnitude_multiplier = {
    '': 1, 'k': 1e3,
    'M': 1e6, 'G': 1e9,
    'm': 1e-3, 'u': 1e-6,
    'µ': 1e-6, 'n': 1e-9
}


def parse_net_file_to_circuit(file_path):
    """
    This function parses a .net file, which contains the definition of a circuit,
    and converts it into a Circuit object that represents the circuit internally.

    Args:
        file_path: The path to the .net file containing the circuit definition.

    Returns:
        A Circuit object that represents the parsed circuit.

    Raises:
        MalformedInputError: If the input file has an invalid format or structure.
    """

    circuit = Circuit()  # Create an empty Circuit object to store the parsed information.
    section_open = None  # Keeps track of the currently open section in the .net file.
    sections_count = {'CIRCUIT': 0, 'TERMS': 0, 'OUTPUT': 0}  # Tracks how many times each section appears.

    # Open the .net file in read mode and iterate over each line.
    with open(file_path, 'r', encoding="utf-8") as file:
        for line in file:
            line = line.strip()  # Remove leading and trailing whitespace.

            # Skip comments and empty lines.
            if line.startswith('#') or not line:
                continue

            # Check if the line indicates the start or end of a section.
            if line == "<CIRCUIT>":
                if section_open or sections_count['CIRCUIT'] > 0:
                    raise MalformedInputError("CIRCUIT section opened improperly or multiple times.")
                section_open = 'CIRCUIT'
                sections_count['CIRCUIT'] += 1
            elif line == "<TERMS>":
                if section_open or sections_count['TERMS'] > 0:
                    raise MalformedInputError("TERMS section opened improperly or multiple times.")
                section_open = 'TERMS'
                sections_count['TERMS'] += 1
            elif line == "<OUTPUT>":
                if section_open or sections_count['OUTPUT'] > 0:
                    raise MalformedInputError("OUTPUT section opened improperly or multiple times.")
                section_open = 'OUTPUT'
                sections_count['OUTPUT'] += 1
            elif line == "</CIRCUIT>":
                if section_open != 'CIRCUIT':
                    raise MalformedInputError("CIRCUIT section closed without being opened.")
                section_open = None
            elif line == "</TERMS>":
                if section_open != 'TERMS':
                    raise MalformedInputError("TERMS section closed without being opened.")
                section_open = None
            elif line == "</OUTPUT>":
                if section_open != 'OUTPUT':
                    raise MalformedInputError("OUTPUT section closed without being opened.")
                section_open = None
            else:  # The line contains data for the currently open section.
                if not section_open:
                    raise MalformedInputError("Data outside of any section.")
                if section_open == 'CIRCUIT':
                    process_circuit_line(line, circuit)
                elif section_open == 'TERMS':
                    process_terms_line(line, circuit)
                elif section_open == 'OUTPUT':
                    process_output_line(line, circuit)

    # Ensure that all sections were properly formatted and closed.
    for section, count in sections_count.items():
        if count != 1:
            raise MalformedInputError(f"{section} section not properly formatted.")

    return circuit


def process_circuit_line(line, circuit):
    """
    Processes a line from the CIRCUIT section of the .net file and adds a
    component to the Circuit object.

    Args:
        line: The line of text to be processed.
        circuit: The Circuit object to add the component to.

    Raises:
        MalformedInputError: If the line has an invalid format or defines an invalid component.
    """
    # Regular expression pattern for matching circuit lines:
    #  - Extracts node numbers (n1 and n2)
    #  - Extracts component type (R, L, C, or G)
    #  - Extracts component value and magnitude prefix
    pattern = r"""
    ^                           # Start of the string
    (?=                         # Start of a positive lookahead for 'n1'
        .*                      # Any character, any number of times
        \bn1\s*=\s*             # 'n1' with optional whitespace around '='
        (?P<n1>\d+)             # Capture one or more digits as 'n1'
        \b                      # Word boundary to ensure a full match
    )
    (?=                         # Start of a positive lookahead for 'n2'
        .*                      # Any character, any number of times
        \bn2\s*=\s*             # 'n2' with optional whitespace around '='
        (?P<n2>\d+)             # Capture one or more digits as 'n2'
        \b                      # Word boundary to ensure a full match
    )
    (?=                         # Start of a positive lookahead for component
        .*                      # Any character, any number of times
        (?P<component>[RLCG])   # Capture 'R', 'L', 'C' or 'G' as component
        \s*=\s*                 # Optional whitespace around '='
        (?P<value>              # Start of the 'value' capture group
            (?:-?\d+            # Optional '-' followed by one or more digits
            (?:\.\d*)?)         # Optional decimal part
            (?:[eE][+-]?\d+)?   # Optional exponent part
        )                       # End of the 'value' capture group
        \s*                     # Optional whitespace
        (?P<magnitude>[kmunµGM]?)   # Capture magnitude prefix, if present
        \b                      # Word boundary to ensure a full match
    )                           # End of lookahead
    .+                          # Ensure the entire string is matched
    """

    regex = re.compile(pattern, re.VERBOSE)

    match = regex.search(line)
    if match:
        data = {k: match.group(k) for k in ('n1', 'n2', 'component', 'value', 'magnitude')}
        # Convert and adjust values
        data['n1'] = int(data['n1'])
        data['n2'] = int(data['n2'])
        data['value'] = float(data['value'])
        data['value'] *= magnitude_multiplier.get(data['magnitude'], 1)
        
        # Check for invalid component connections
        if data['n1'] == data['n2']:
            raise MalformedInputError(f"Invalid component: {line}")
        if 0 not in (data['n1'], data['n2']) and abs(data['n1'] - data['n2']) != 1:
            raise MalformedInputError(f"Invalid component: {line}")

        # Add the component to the circuit
        circuit.add_component(data['component'], data['n1'], data['n2'], data['value'])
    else:
        raise MalformedInputError(f"Invalid circuit line: {line}")


def process_terms_line(line, circuit):
    """
    Processes a line from the TERMS section of the .net file and sets
    termination parameters in the Circuit object.

    Args:
        line: The line of text to be processed.
        circuit: The Circuit object to set the termination parameters in.

    Raises:
        MalformedInputError: If the line has an invalid format or contains an unknown termination parameter.
    """
    # Regular expression pattern for matching termination lines:
    #  - Extracts term name (alphanumeric and underscore)
    #  - Extracts term value and magnitude prefix
    terms_pattern = re.compile(r"""
        (?P<term>\w+)       # Term name (alphanumeric and underscore)
        \s*=\s*             # Equals sign with optional whitespace on both sides
        (?P<value>          # Start of value capture group
            (-?)            # Optional sign (negative)
            \d+             # One or more digits before the decimal point
            \.?             # Optional decimal point
            \d*             # Zero or more digits after the decimal point
            (?:[eE][+-]?\d+)? # Optional scientific notation (e.g., e+10, E-10)
        )                   # End of value capture group
        \s*                 # Optional whitespace
        (?P<magnitude>      # Start of magnitude prefix capture group
            [kmunµGM]?      # Optional single character for magnitude prefix (k, m, u, n, µ, G, M)
        )                   # End of magnitude prefix capture group
    """, re.VERBOSE)

    matches = terms_pattern.finditer(line)
    if matches:
        for match in matches:
            term = match.group('term')
            magnitude = match.group('magnitude')
            value = float(match.group('value')) * magnitude_multiplier.get(magnitude, 1)
            circuit.set_termination(term, value)
    else:
        raise MalformedInputError(f"Invalid terms line: {line}")


def process_output_line(line, circuit):
    """
    Processes a line from the OUTPUT section of the .net file and adds an output parameter 
    to the Circuit object.

    Args:
        line: The line of text to be processed.
        circuit: The Circuit object to add the output parameter to.

    Raises:
        MalformedInputError: If the line has an invalid format.
    """
    # Regular expression pattern for matching output lines:
    #  - Extracts output parameter name
    #  - Extracts optional dB indicator
    #  - Extracts optional magnitude prefix
    #  - Extracts unit
    pattern = r"""
        ^                   # Start of the line
        (?P<name>\w+)       # Capture the name (parameter)
        \s*                 # Optional whitespace
        (?P<is_db>dB)?      # Optional dB indicator
        \s*             # Equals sign with optional whitespace on both sides
        (?P<magnitude>[mkMGuµn])? # Optional magnitude prefix
        \s*                 # Optional whitespace
        (?P<unit>[AVWOhms]*) # Capture the unit
        $                   # End of the line
    """

    regex = re.compile(pattern, re.VERBOSE)
    match = regex.match(line)

    if match:
        name = match.group('name')
        is_db = bool(match.group('is_db'))
        magnitude = match.group('magnitude') if match.group('magnitude') else ''
        unit = match.group('unit') if match.group('unit') else ''

        circuit.add_output(name, unit, magnitude, is_db)
    else:
        raise MalformedInputError(f"Invalid output line: {line}")