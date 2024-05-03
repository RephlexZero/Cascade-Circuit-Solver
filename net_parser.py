# Author: Jake Stewart
# Email: js3910@bath.ac.uk
# License: MIT
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
    def __init__(self, message):
        super().__init__("Malformed Input: " + message)


# A dictionary that maps magnitude prefixes to their corresponding numerical factors.
# This is used to convert component values and termination parameters from their
# string representations to numerical values with appropriate scaling.
magnitude_multiplier = {
    '': 1, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12, 'P': 1e15,
    'm': 1e-3, 'u': 1e-6, 'µ': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15
}


def parse_net_file_to_circuit(file_path):
    """
    This function parses a .net file, which contains the definition of a circuit,
    and converts it into a Circuit object that represents the circuit internally.
    """

    circuit = Circuit()  # Create an empty Circuit object to store the parsed information.
    section_open = None  # Keeps track of the currently open section in the .net file.
    # Open the .net file in read mode and iterate over each line.
    with open(file_path, 'r', encoding="utf-8") as file:
        for line in file:
            line = line.strip()  # Remove leading and trailing whitespace.

            # Skip comments and empty lines.
            if line.startswith('#') or not line:
                continue

            # Check if the line indicates the start or end of a section.
            match line:
                case "<CIRCUIT>":
                    if section_open:
                        raise MalformedInputError("CIRCUIT section opened improperly or multiple times.")
                    section_open = 'CIRCUIT'
                    # print("<CIRCUIT>")
                case "<TERMS>":
                    if section_open:
                        raise MalformedInputError("TERMS section opened improperly or multiple times.")
                    section_open = 'TERMS'
                    # print("<TERMS>")
                case "<OUTPUT>":
                    if section_open:
                        raise MalformedInputError("OUTPUT section opened improperly or multiple times.")
                    section_open = 'OUTPUT'
                    # print("<OUTPUT>")
                case "</CIRCUIT>":
                    if section_open != 'CIRCUIT':
                        raise MalformedInputError("CIRCUIT section closed without being opened.")
                    section_open = None
                    # print("</CIRCUIT>\n")
                case "</TERMS>":
                    if section_open != 'TERMS':
                        raise MalformedInputError("TERMS section closed without being opened.")
                    section_open = None
                    # print("</TERMS>\n")
                case "</OUTPUT>":
                    if section_open != 'OUTPUT':
                        raise MalformedInputError("OUTPUT section closed without being opened.")
                    section_open = None
                    # print("</OUTPUT>\n")
                case _:
                    # Process lines based on the currently open section.
                    match section_open:
                        case 'CIRCUIT':
                            process_circuit_line(line, circuit)
                        case 'TERMS':
                            process_terms_line(line, circuit)
                        case 'OUTPUT':
                            process_output_line(line, circuit)
                        case _:
                            raise MalformedInputError(f"Data found outside of a section: {line}")
    return circuit

def make_regex_list(l):
    """
    This function takes a list of strings and returns a regex pattern that matches any of the strings.
    """
    return '|'.join(map(str, map(re.escape, l)))

magnitudes = make_regex_list(["k", "M", "G", "T", "m", "u", "µ", "n", "p", "f"])
# Regular expression pattern for matching circuit lines:
#  - Extracts node numbers (n1 and n2)
#  - Extracts component type (R, L, C, or G)
#  - Extracts component value and magnitude prefix
components = make_regex_list(["R", "L", "C", "G"])
component_pattern = re.compile(rf"""
    (n1\s*=\s*(?P<n1>\d+))\s*                   # Node 1 number
    (n2\s*=\s*(?P<n2>\d+))\s*                   # Node 2 number
    ((?P<component>{components})                # Component type
    \s*=\s*                                     # Equals sign with optional whitespace on both sides
    (?P<value>-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?) # Scientific notation number
    \s*                                         # Optional whitespace
    (?P<magnitude>{magnitudes})?)               # Optional magnitude prefix
""", re.VERBOSE)

def process_circuit_line(line, circuit):
    """
    Processes a line from the CIRCUIT section of the .net file and adds a
    component to the Circuit object.
    """

    match = component_pattern.match(line)
    if match:
        total_matched_length = match.end() - match.start()
        if total_matched_length != len(line):
            raise MalformedInputError(f"Invalid terms line, not fully valid: {line}")
        data = match.groupdict()

        n1 = int(data["n1"])
        n2 = int(data["n2"])
        component = data['component']
        magnitude = data["magnitude"]
        value = float(data["value"]) * magnitude_multiplier.get(magnitude, 1)

        # Check for invalid component connections
        if n1 == n2:
            raise MalformedInputError(f"Component forms self-loop: {line}")
        if 0 not in [n1, n2] and abs(n1 - n2) != 1:
            raise MalformedInputError(f"Component nodes cannot be more than 1 value apart if not in shunt: {line}")

        circuit.add_component(n1, n2, component, value)
        # print(f"n1={n1} n2={n2} {component}={value} {magnitude}")
    else:
        raise MalformedInputError(f"Invalid circuit line: {line}")

# Regular expression pattern for matching terms lines:
#  - Extracts term name
#  - Extracts term value
#  - Extracts optional magnitude prefix
# Creating a non-capturing group with an alternation structure for the terms
terms = make_regex_list(["Fstart", "Fend", "LFstart", "LFend", "Nfreqs", "VT", "RS", "RL", "IN", "GS"])
terms_pattern = re.compile(rf"""
    \s*
    (?P<term>{terms})                           # Only matches specified terms
    \s*=\s*                                     # Equals sign with optional whitespace on both sides
    (?P<value>-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?) # Scientific notation number
    \s*                                         # Optional whitespace
    (?P<magnitude>{magnitudes})?                # Optional magnitude prefix
""", re.VERBOSE)

def process_terms_line(line, circuit):
    """
    Processes a line from the TERMS section of the .net file and sets
    termination parameters in the Circuit object.
    """
    matches = list(terms_pattern.finditer(line))
    total_matched_length = sum(match.end() - match.start() for match in matches)
    if  total_matched_length != len(line):
        raise MalformedInputError(f"Invalid terms line, not fully valid: {line}")
    
    if matches:
        for match in matches:
            term_data = match.groupdict()
            name = term_data['term']
            magnitude = term_data['magnitude']
            value = float(term_data['value']) * magnitude_multiplier.get(magnitude, 1)
            
            circuit.set_termination(name, value)
            # print(f"{name}={value}{magnitude}")
    else:
        raise MalformedInputError(f"Invalid terms line: {line}")

# Regular expression pattern for matching output lines:
#  - Extracts output parameter name
#  - Extracts optional dB indicator
#  - Extracts optional magnitude prefix
#  - Extracts unit
outputs = make_regex_list(["Vout", "Iout", "Vin", "Iin", "Zin", "Zout", "Pin", "Pout", "Av", "Ai", "Ap"])
units = make_regex_list(["V", "A", "W", "Ohms"])
output_pattern = re.compile(rf"""
    ^                                           # Start of the line
    (?P<name>{outputs})                         # Capture the name (parameter)
    \s*                                         # Optional whitespace
    (?P<is_db>dB)?                              # Optional dB indicator
    \s*                                         # Equals sign with optional whitespace on both sides
    (?P<magnitude>{magnitudes})?                # Optional magnitude prefix
    \s*                                         # Optional whitespace
    (?P<unit>{units})?                          # Capture the unit
    $                                           # End of the line
""", re.VERBOSE)

def process_output_line(line, circuit):
    """
    Processes a line from the OUTPUT section of the .net file and adds an output parameter 
    to the Circuit object.
    """
    match = output_pattern.match(line)

    if match:
        output_data = match.groupdict()
        name = output_data['name']
        is_db = bool(output_data['is_db'])
        magnitude = output_data['magnitude'] if output_data['magnitude'] else ''
        unit = output_data['unit'] if output_data['unit'] else ''

        circuit.add_output(name, unit, magnitude, is_db)
        # print(f"{name} {'dB' if is_db else ''}{magnitude}{unit}")
    else:
        raise MalformedInputError(f"Invalid output line: {line}")