from functools import reduce
import numpy as np


class Circuit:
    def __init__(self):
        self.components = []
        self.outputs = []
        self.terminations = Terminations()

        self.frequency = None
        self.s = np.cdouble(0)

        self.ABCD = None

    def solve(self, f):
        self.frequency = f
        self.s = 2j * np.pi * self.frequency
        self.resolve_matrix(self.s)
        self.terminations.calculate_outputs(self.ABCD)

        for output in self.outputs:
            match output.name:
                case 'Zin':
                    output.value = self.terminations.ZI
                case 'Zout':
                    output.value = self.terminations.ZO
                case 'Vin':
                    output.value = self.terminations.V1
                case 'Vout':
                    output.value = self.terminations.V2
                case 'Iin':
                    output.value = self.terminations.I1
                case 'Iout':
                    output.value = self.terminations.I2
                case 'Pin':
                    output.value = self.terminations.PI
                case 'Pout':
                    output.value = self.terminations.PO
                case 'Zin':
                    output.value = self.terminations.ZI
                case 'Zout':
                    output.value = self.terminations.ZO
                case 'Av':
                    output.value = self.terminations.AV
                case 'Ai':
                    output.value = self.terminations.AI
                case 'Ap':
                    output.value = self.terminations.AP
                case _:
                    raise ValueError(f"Unknown output parameter: {output.name}")
        return self.outputs

    def add_component(self, component, n1, n2, value):
        self.components.append(Component(component, n1, n2, value))

    def set_termination(self, name, value):
        setattr(self.terminations, name, value)

    def add_output(self, name, unit, magnitude, is_db):
        self.outputs.append(Output(name, unit, magnitude, is_db))

    def resolve_matrix(self, s=0):
        circuit_matrices = [component.get_abcd_matrix(s) for component in self.components]
        if len(circuit_matrices) == 0:
            self.ABCD = np.eye(2)
        elif len(circuit_matrices) == 1:
            self.ABCD = np.array(circuit_matrices)
        elif len(circuit_matrices) > 1:
            self.ABCD = reduce(np.matmul, circuit_matrices)

    def sort_components(self):
        def custom_sort_key(component):
            # Extract n1 and n2, ignoring zeros
            numbers = [n for n in [component.n1, component.n2] if n != 0]
            # Handle different cases based on the number of nonzero elements
            match len(numbers):
                case 0:  # Both numbers are zero
                    return (0, 0)
                case 1:  # Only one nonzero number
                    return (numbers[0], 0)
                case 2:  # Both numbers are nonzero; sort them to find the lowest and then the other
                    numbers_sorted = sorted(numbers)
                    return (numbers_sorted[0], numbers_sorted[1])
                case _:
                    raise ValueError("Invalid number of nonzero elements")

        self.components = sorted(self.components, key=custom_sort_key)

class Component:
    def __init__(self, type, n1, n2, value):

        self.type = type
        self.n1 = n1
        self.n2 = n2
        self.value = value

    def get_abcd_matrix(self, s):
        is_shunt = self.n1 == 0 or self.n2 == 0

        match self.type:
            case 'R':  # Resistor
                Z = self.value
                if is_shunt:
                    abcd_matrix = np.array([[1, 0],
                                            [1 / Z, 1]])
                else:
                    abcd_matrix = np.array([[1, Z],
                                            [0, 1]])
            case 'L':  # Inductor
                sL = s * self.value
                if is_shunt:
                    abcd_matrix = np.array([[1, 0],
                                            [1 / sL, 1]])
                else:
                    abcd_matrix = np.array([[1, sL],
                                            [0, 1]])
            case 'C':  # Capacitor
                sC = s * self.value
                if is_shunt:
                    abcd_matrix = np.array([[1, 0],
                                            [sC, 1]])
                else:
                    abcd_matrix = np.array([[1, 1 / sC],
                                            [0, 1]])
            case 'G':  # Conductance
                Y = self.value
                if is_shunt:
                    abcd_matrix = np.array([[1, 0],
                                            [Y, 1]])
                else:
                    abcd_matrix = np.array([[1, 1 / Y],
                                            [0, 1]])
            case _:  # Unknown component type
                raise ValueError(f"Unknown component type: {self.type}")
        return abcd_matrix

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

        self.LFstart = None
        self.LFend = None

        self.Nfreqs = None
        
        self.AV = None
        self.AI = None
        self.AP = None
        
        self.PI = None
        self.PO = None

    def calculate_outputs(self, ABCD):
        A, B, C, D = ABCD.flatten()
        
        if self.RL:
            self.ZI = (A * self.RL + B) / (C * self.RL + D)
        else:
            raise ValueError("RL must be provided")

        if self.VT and self.RS:
            self.ZO = (D * self.RS + B) / (C * self.RS + A)
            self.I1 = self.VT / (self.RS + self.ZI)
            self.V1 = self.VT - self.I1 * self.RS
        elif self.IN and self.GS:
            self.ZO = (C + self.GS * A) / (D + self.GS * B)
            self.V1 = self.IN * (self.ZI / (1 + self.ZI * self.GS))
            self.I1 = self.IN - self.V1 * self.GS
        else:
            raise ValueError("RL and either VT and RS or IN and GS must be provided")
        
        input_vector = np.array([[self.V1], [self.I1]])

        ABCD_inv = np.linalg.inv(ABCD)
        
        output_vector = ABCD_inv @ input_vector
        self.V2, self.I2 = output_vector.flatten()
        
        self.AV = self.RL / (A * self.RL + B)
        self.AI = 1 / (C * self.RL + D)
        self.AP = self.AV * np.conj(self.AI)
        
        self.PI = self.V1 * np.conj(self.I1)
        self.PO = self.V2 * np.conj(self.I2)

class Output:
    def __init__(self, name, unit, magnitude, is_db):
        self.name = name  # Output parameter name, e.g., Vin, Vout, etc.
        self.value = None  # Value of the output parameter (calculated later)
        self.unit = unit  # Unit of the parameter, e.g., V (Volts), A (Amps), etc.
        self.magnitude = magnitude  # Magnitude prefix, e.g., k (kilo), m (milli), etc.
        self.is_db = is_db  # Boolean indicating if the output is in dB
