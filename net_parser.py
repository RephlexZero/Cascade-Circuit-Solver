import re
from circuit import Circuit


class MalformedInputError(Exception):
    pass


magnitude_multiplier = {
    '': 1, 'k': 1e3,
    'M': 1e6, 'G': 1e9,
    'm': 1e-3, 'u': 1e-6,
    'µ': 1e-6, 'n': 1e-9
}


def parse_net_file_to_circuit(file_path):

    circuit = Circuit()
    section_open = None
    sections_count = {'CIRCUIT': 0, 'TERMS': 0, 'OUTPUT': 0}

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line:
                continue  # Skip comments and empty lines

            match line:
                case "<CIRCUIT>":
                    if section_open or sections_count['CIRCUIT'] > 0:
                        raise MalformedInputError("CIRCUIT section opened improperly or multiple times.")
                    section_open = 'CIRCUIT'
                    sections_count['CIRCUIT'] += 1
                case "<TERMS>":
                    if section_open or sections_count['TERMS'] > 0:
                        raise MalformedInputError("TERMS section opened improperly or multiple times.")
                    section_open = 'TERMS'
                    sections_count['TERMS'] += 1
                case "<OUTPUT>":
                    if section_open or sections_count['OUTPUT'] > 0:
                        raise MalformedInputError("OUTPUT section opened improperly or multiple times.")
                    section_open = 'OUTPUT'
                    sections_count['OUTPUT'] += 1
                case "</CIRCUIT>":
                    if section_open != 'CIRCUIT':
                        raise MalformedInputError("CIRCUIT section closed without being opened.")
                    section_open = None
                case "</TERMS>":
                    if section_open != 'TERMS':
                        raise MalformedInputError("TERMS section closed without being opened.")
                    section_open = None
                case "</OUTPUT>":
                    if section_open != 'OUTPUT':
                        raise MalformedInputError("OUTPUT section closed without being opened.")
                    section_open = None
                case _:
                    if not section_open:
                        raise MalformedInputError("Data outside of any section.")
                    match section_open:
                        case 'CIRCUIT':
                            process_circuit_line(line, circuit)
                        case 'TERMS':
                            process_terms_line(line, circuit)
                        case 'OUTPUT':
                            process_output_line(line, circuit)

    # After processing all lines, check if all sections were properly closed
    for section, count in sections_count.items():
        if count != 1:
            raise MalformedInputError(f"{section} section not properly formatted.")

    return circuit


def process_circuit_line(line, circuit):
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
        (?P<component>[RLCG])    # Capture 'R', 'L', 'C' or 'G' as component
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
    """  # End of the pattern

    regex = re.compile(pattern, re.VERBOSE)

    match = regex.search(line)
    if match:
        data = {k: match.group(k) for k in ('n1', 'n2', 'component', 'value', 'magnitude')}
        # Convert and adjust values
        data['n1'] = int(data['n1'])
        data['n2'] = int(data['n2'])
        data['value'] = float(data['value'])
        data['value'] *= magnitude_multiplier.get(data['magnitude'], 1)

        # Extract only the necessary components
        component_data = {k: data[k] for k in ('component', 'n1', 'n2', 'value')}
        circuit.add_component(**component_data)
    else:
        raise MalformedInputError(f"Invalid circuit line: {line}")


def process_terms_line(line, circuit):
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
            setattr(circuit.terminations, term, value)
    else:
        raise MalformedInputError(f"Invalid terms line: {line}")


def process_output_line(line, circuit):
    # Updated regex pattern to accurately parse the input lines
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

    # Compile the regex with VERBOSE flag to allow whitespace and comments
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
