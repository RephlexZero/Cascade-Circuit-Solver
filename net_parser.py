import re
from circuit import Circuit

class MalformedInputError(Exception):
    pass

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
    magnitude_multiplier = {
        '': 1,
        'm': 1e-3, 'u': 1e-6, 'n': 1e-9,
        'k': 1e3, 'M': 1e6, 'G': 1e9
    }

    pattern = r"""
        (?: 
            n1\s*=\s*(?P<n1>\d+)\s+ 
            | n2\s*=\s*(?P<n2>\d+)\s+
            | (?P<component>[RLCG])\s*= 
        ){3} 
        (?P<value>(-?)\d+\.?\d*(?:[eE][+-]?\d+)?)  # Value (includes scientific notation)
        \s*
        (?P<magnitude>[kmunµGM]?)  # Optional magnitude prefix
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

        # Extract only the necessary components
        component_data = {k: data[k] for k in ('component', 'n1', 'n2', 'value')}
        circuit.add_component(**component_data) 

def process_terms_line(line, circuit):
    
    magnitude_multipliers = {
        '': 1,   # Base case, no magnitude prefix
        'k': 1e3, 'M': 1e6, 'G': 1e9, 
        'm': 1e-3, 'u': 1e-6, 'n': 1e-9
    }
    
    terms_pattern = re.compile(r"""
        (?P<term>\w+)       # Term name (alphanumeric and underscore)
        \s*=\s*             # Equals sign with optional whitespace
        (?P<value>(-?)\d+\.?\d*(?:[eE][+-]?\d+)?)  # Value (includes scientific notation)
        \s*
        (?P<magnitude>[kmunµGM]?)  # Optional magnitude prefix
    """, re.VERBOSE)

    matches = terms_pattern.finditer(line)

    for match in matches:
        term = match.group('term')
        value = float(match.group('value')) * magnitude_multipliers.get(match.group('magnitude'), 1)
        setattr(circuit.terminations, term, value)  # Assuming 'terminations' is correct 




def process_output_line(line, circuit):
    # Updated regex pattern to accurately parse the input lines
    pattern = r"""
        ^                   # Start of the line
        (?P<name>\w+)       # Capture the name (parameter)
        \s*                 # Optional whitespace
        (?P<is_db>dB)?      # Optional dB indicator
        (?P<magnitude>[mkMGuµn])? # Optional magnitude prefix
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
        raise ValueError(f"Invalid output line: {line}")