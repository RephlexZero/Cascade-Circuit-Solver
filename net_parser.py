import re
from circuit import Circuit

def parse_net_file_to_circuit(file_path):
    circuit = Circuit()
    section = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line:
                continue  # Skip comments and empty lines

            match line:
                case "<CIRCUIT>":
                    section = 'CIRCUIT'
                case "<TERMS>":
                    section = 'TERMS'
                case "<OUTPUT>":
                    section = 'OUTPUT'
                case "</CIRCUIT>":
                    section = None
                case "</TERMS>":
                    section = None
                case "</OUTPUT>":
                    section = None
                case _:
                    match section:
                        case 'CIRCUIT':
                            process_circuit_line(line, circuit)
                        case 'TERMS':
                            process_terms_line(line, circuit)
                        case 'OUTPUT':
                            process_output_line(line, circuit)
                        case _:
                            continue

    return circuit

def process_circuit_line(line, circuit):
    component_matches = re.findall(r'(n1|n2|R|G|L|C)=([\d\.e+-]+)', line)
    for key, value in component_matches:
        if key == 'n1':
            n1 = int(value)
        elif key == 'n2':
            n2 = int(value)
        elif key in ['R', 'G', 'L', 'C']:
            component_type = key
            value = float(value)

    circuit.add_component(component_type, n1, n2, value)

def process_terms_line(line, circuit):
    terms = re.findall(r'(\w+)=(\S+)', line)
    for term, value in terms:
        setattr(circuit.terminations, term, float(value))

def process_output_line(line, circuit):
    name, *unit = line.split()
    unit = unit[0] if unit else None
    circuit.add_output(name, unit)
