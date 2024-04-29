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
    '': 1, 'k': 1e3,
    'M': 1e6, 'G': 1e9,
    'm': 1e-3, 'u': 1e-6,
    'µ': 1e-6, 'n': 1e-9
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

# Regular expression pattern for matching circuit lines:
#  - Extracts node numbers (n1 and n2)
#  - Extracts component type (R, L, C, or G)
#  - Extracts component value and magnitude prefix
component_pattern = re.compile(r"""
^                                  # Start of the string
    (?=.*\bn1\s*=\s*(?P<n1>\d+)\b)     # Positive lookahead for 'n1'
    (?=.*\bn2\s*=\s*(?P<n2>\d+)\b)     # Positive lookahead for 'n2'
    (?=.*(?P<component>[RLCG])
\s*=\s*
(?P<value>-?\d+(?:.\d*)?(?:[eE][+-]?\d+)?)\s*(?P<magnitude>[kmunµGM]?)\b) # Lookahead for the component, value, and magnitude
.+ # Consume the entire string
$ # End of the string
""", re.VERBOSE)

# Regular expression pattern for matching terms lines:
#  - Extracts term name
#  - Extracts term value
#  - Extracts optional magnitude prefix
terms_pattern = re.compile(r"""
    \s*
    (?P<term>\w+)                 # Term name (alphanumeric and underscore)
    \s*=\s*                       # Equals sign with optional whitespace on both sides
    (?P<value>                    # Start of value capture group
        -?\d+                     # Optional negative sign and one or more digits
        (?:\.\d*)?                # Optional decimal and fractional part
        (?:[eE][+-]?\d+)?         # Optional exponent
    )
    \s*                           # Optional whitespace
    (?P<magnitude>[kmunµGM]?)     # Optional magnitude prefix
""", re.VERBOSE)

# Regular expression pattern for matching output lines:
#  - Extracts output parameter name
#  - Extracts optional dB indicator
#  - Extracts optional magnitude prefix
#  - Extracts unit
output_pattern = re.compile(r"""
    ^                         # Start of the line
    (?P<name>\w+)             # Capture the name (parameter)
    \s*                       # Optional whitespace
    (?P<is_db>dB)?            # Optional dB indicator
    \s*                       # Equals sign with optional whitespace on both sides
    (?P<magnitude>[mkMGuµn])? # Optional magnitude prefix
    \s*                       # Optional whitespace
    (?P<unit>[AVWOhms]*)      # Capture the unit
    $                         # End of the line
""", re.VERBOSE)

def process_circuit_line(line, circuit):
    """
    Processes a line from the CIRCUIT section of the .net file and adds a
    component to the Circuit object.
    """

    match = component_pattern.search(line)
    if match:
        data = match.groupdict()

        data['n1'] = int(data['n1'])
        data['n2'] = int(data['n2'])
        data['value'] = float(data['value'])

        # Check for invalid component connections
        if data['n1'] == data['n2']:
            raise MalformedInputError(f"Invalid component nodes: {line}")
        if 0 not in [data['n1'], data['n2']] and abs(data['n1'] - data['n2']) != 1:
            raise MalformedInputError(f"Invalid component nodes: {line}")

        circuit.add_component(data['component'], data['n1'], data['n2'],
                              data['value'] * magnitude_multiplier.get(data['magnitude'], 1))
        # print(f"n1={data['n1']} n2={data['n2']} {data['component']}={data['value']} {data['magnitude']}")
    else:
        raise MalformedInputError(f"Invalid circuit line: {line}")


def process_terms_line(line, circuit):
    """
    Processes a line from the TERMS section of the .net file and sets
    termination parameters in the Circuit object.
    """
    matches = terms_pattern.finditer(line)
    if matches:
        for match in terms_pattern.finditer(line):
            term_data = match.groupdict()
            # Extract values using groupdict and set them in the Circuit object
            value = float(term_data['value']) * magnitude_multiplier.get(term_data['magnitude'], 1)
            circuit.set_termination(term_data['term'], value)
            # print(f"{term_data['term']}={term_data['value']}{term_data['magnitude']}")
    else:
        raise MalformedInputError(f"Invalid terms line: {line}")

def process_output_line(line, circuit):
    """
    Processes a line from the OUTPUT section of the .net file and adds an output parameter 
    to the Circuit object.
    """
    match = output_pattern.match(line)

    if match:
        name = match.group('name')
        is_db = bool(match.group('is_db'))
        magnitude = match.group('magnitude') if match.group('magnitude') else ''
        unit = match.group('unit') if match.group('unit') else ''

        circuit.add_output(name, unit, magnitude, is_db)
        # print(f"{name} {'dB' if is_db else ''}{magnitude}{unit}")
    else:
        raise MalformedInputError(f"Invalid output line: {line}")