import numpy as np
from functools import reduce

class Component:
    def __init__(self, type, n1, n2, value):
        self.type = type  # R, L, C, G
        self.n1 = n1      # Node 1
        self.n2 = n2      # Node 2
        self.value = value  # Value of the component

    def get_abcd_matrix(self, s=0):
        is_shunt = 0 in [self.n1, self.n2]  # Check if the component is in shunt configuration with ground
        
        match self.type:
            case 'R':
                if not is_shunt:
                    abcd = np.array([[1, self.value], [0, 1]])  
                else:
                    abcd = np.array([[1, 0], [1 / self.value, 1]])
            case 'L':
                if not is_shunt:
                    abcd = np.array([[1, 0], [s * self.value, 1]]) if s != 0 else np.array([[1, 0], [0, 1]])
                else:
                    abcd = np.array([[1, 0], [1 / (s * self.value), 1]]) if s != 0 else np.array([[1, 0], [np.inf, 1]])
            case 'C':
                if not is_shunt:
                    abcd = np.array([[1, 1 / (s * self.value)], [0, 1]]) if s != 0 else np.array([[1, np.inf], [0, 1]])
                else:
                    abcd = np.array([[1, 0], [s * self.value, 1]]) if s != 0 else np.array([[1, 0], [0, 1]])
            case 'G':
                if not is_shunt:
                    abcd = np.array([[1, 1 / self.value], [0, 1]])
                else:
                    abcd = np.array([[1, 0], [self.value, 1]])
            case _:
                raise ValueError("Unknown component type")
        return abcd
    
class Termination:
    def __init__(self, type, value):
        self.type = type  # VT, RS, IN, GS, RL, Fstart, Fend, Nfreqs
        self.value = value

class Output:
    def __init__(self, name, unit=None):
        self.name = name  # Output parameter name, e.g., Vin, Vout, etc.
        self.unit = unit  # Unit of the parameter, e.g., V (Volts), A (Amps), etc.

class Circuit:
    def __init__(self):
        self.components = []
        self.terminations = {}
        self.outputs = []
        
    def add_component(self, type, n1, n2, value):
        self.components.append(Component(type, n1, n2, value))

    def set_termination(self, type, value):
        self.terminations[type] = Termination(type, value)

    def add_output(self, name, unit):
        self.outputs.append(Output(name, unit))

def custom_matmul(matrices):
    # Filter or adjust matrices containing 'inf' before multiplication
    filtered_matrices = [mat for mat in matrices if not np.isinf(mat).any()]
    
    # If filtering results in an empty list, handle accordingly
    if not filtered_matrices:
        return None  # or an appropriate default matrix, depending on your application
    
    # Perform multiplication with the filtered/adjusted list
    result = reduce(np.matmul, filtered_matrices)
    return result