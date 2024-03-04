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
    component_matches = re.findall(r'(n1|n2|R|G|L|C)=([\d\.e+-]+)', line)
    n1, n2, type, value = None, None, None, None
    for key, value in component_matches:
        if key == 'n1':
            n1 = int(value)
        elif key == 'n2':
            n2 = int(value)
        elif key in ['R', 'G', 'L', 'C']:
            type = key
            value = float(value)
    if None not in [n1, n2, type, value]:
        circuit.add_component(type, n1, n2, value)
    else:
        raise ValueError(f"Invalid component line: {line}")

def process_terms_line(line, circuit):
    terms = re.findall(r'(\w+)=(\S+)', line)
    for term, value in terms:
        setattr(circuit.terminations, term, float(value))

def process_output_line(line, circuit):
    name, *unit = line.split()
    unit = unit[0] if unit else None
    circuit.add_output(name, unit)
