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
                case "</CIRCUIT>":
                    section = None
                case "<TERMS>":
                    section = 'TERMS'
                case "</TERMS>":
                    section = None
                case "<OUTPUT>":
                    section = 'OUTPUT'
                case "</OUTPUT>":
                    section = None
                case _ if section == 'CIRCUIT':
                    component_matches = re.findall(r'(n1|n2|R|G|L|C)=([\d\.e+-]+)', line)
                    for key, value in component_matches:
                        if key in ['R', 'G', 'L', 'C']:
                            component_type = key
                            value = float(value)
                        elif key == 'n1':
                            n1 = int(value)
                        elif key == 'n2':
                            n2 = int(value)
                    circuit.add_component(component_type, n1, n2, value)

                case _ if section == 'TERMS':
                    terms = re.findall(r'(\w+)=(\S+)', line)  # Find all term-value pairs on the line
                    for term, value in terms:
                        circuit.set_termination(term, float(value))

                case _ if section == 'OUTPUT':
                    name, *unit = line.split()
                    unit = unit[0] if unit else None
                    circuit.add_output(name, unit)

    return circuit