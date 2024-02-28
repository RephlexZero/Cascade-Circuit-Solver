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
    
class Terminations:
    def __init__(self):
        self.ZI = None
        self.ZO = None
        
        self.V1 = None
        self.V2 = None
        self.I1 = None
        self.I2 = None
        
        self.VT = None
        self.RS = None
        
        self.IN = None
        self.GS = None
        
        self.RL = None

        self.Fstart = None
        self.Fend = None
        self.Nfreqs = None
    
    def calculate_outputs(self, T):
        A, B, C, D = T[0][0], T[0][1], T[1][0], T[1][1]
        
        self.ZI = (A * self.RL + B) / (C * self.RL + D)
        self.ZO = (D * self.RS + B) / (C * self.RS + A)
        
        # Check that VT and RS are provided, or IN and GS are provided
        if self.VT is not None and self.RS is not None:
            self.I1 = self.VT/(self.RS + self.ZI)
            self.V1 = self.VT - self.I1 * self.ZI
        elif self.IN is not None and self.GS is not None:
            self.V1 = self.IN * (self.ZI/(1+self.ZI*self.GS))
            self.I1 = self.IN - self.V1 * self.GS
        else:
            raise ValueError("RL and either VT and RS or IN and GS must be provided")
        
        input_vector = np.array([[self.V1], [self.I1]])
        output_vector = np.matmul(np.linalg.inv(T), input_vector)
        
        self.V2, self.I2 = output_vector[0], output_vector[1]

class Output:
    def __init__(self, name, unit=None):
        self.name = name  # Output parameter name, e.g., Vin, Vout, etc.
        self.unit = unit  # Unit of the parameter, e.g., V (Volts), A (Amps), etc.

class Circuit:
    def __init__(self):
        self.components = []
        self.outputs = []
        self.terminations = Terminations()

        self.T = None
        
    def solve(self, s=0):
        self.resolve_matrix(s)
        self.terminations.calculate_outputs(self.T)
        return self.terminations
        
    def add_component(self, type, n1, n2, value):
        self.components.append(Component(type, n1, n2, value))
        
    def set_termination(self, type, value):
        setattr(self.terminations, type, value)

    def add_output(self, name, unit):
        self.outputs.append(Output(name, unit))

    def resolve_matrix(self, s=0):
        circuit_matricies = [component.get_abcd_matrix(s) for component in self.components]
        self.T = custom_matmul(circuit_matricies)
        
    def sort_components(self):
        self.components = sorted(self.components, key=lambda x: (x.n1, x.n2))

def custom_matmul(matrices):
    # Filter or adjust matrices containing 'inf' before multiplication
    filtered_matrices = [mat for mat in matrices if not np.isinf(mat).any()]
    
    # If filtering results in an empty list, handle accordingly
    if not filtered_matrices:
        return None  # or an appropriate default matrix, depending on your application
    
    # Perform multiplication with the filtered/adjusted list
    result = reduce(np.matmul, filtered_matrices)
    return result