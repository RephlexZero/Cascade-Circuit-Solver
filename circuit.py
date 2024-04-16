from functools import reduce
import numpy as np


class Circuit:
    """
    Represents an electrical circuit with components, terminations, and outputs.

    This class provides methods to add components, set terminations, calculate
    the ABCD matrix and output values for given frequencies.
    """

    def __init__(self):
        self.components = []
        self.outputs = []
        self.terminations = Terminations()

        self.frequency = None
        self.s = np.cdouble(0)

        self.ABCD = None

    def solve(self, f):
        """
        Solves the circuit for a given frequency and calculates output values.

        Args:
            f: The frequency in Hz.

        Returns:
            A list of Output objects containing the calculated values.
        """
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
        """
        Adds a component to the circuit.

        Args:
            component: The type of component ('R', 'L', 'C', or 'G').
            n1: The first node number the component is connected to.
            n2: The second node number the component is connected to.
            value: The value of the component.
        """
        self.components.append(Component(component, n1, n2, value))

    def set_termination(self, name, value):
        """
        Sets a termination parameter (source, load, or frequency).

        Args:
            name: The name of the termination parameter.
            value: The value of the parameter.
        """
        setattr(self.terminations, name, value)

    def add_output(self, name, unit, magnitude, is_db):
        """
        Adds an output parameter to be calculated.

        Args:
            name: The name of the output parameter (e.g., Vin, Zout).
            unit: The unit of the parameter (e.g., V, A, Ohm).
            magnitude: The magnitude prefix (e.g., k, m, '').
            is_db: Whether the output should be expressed in dB.
        """
        self.outputs.append(Output(name, unit, magnitude, is_db))

    def resolve_matrix(self, s=0):
        """
        Calculates the overall ABCD matrix for the circuit.

        Args:
            s: The complex frequency (optional, defaults to 0).
        """
        circuit_matrices = [component.get_abcd_matrix(s) for component in self.components]
        if len(circuit_matrices) == 0:
            self.ABCD = np.eye(2)
        elif len(circuit_matrices) == 1:
            self.ABCD = np.array(circuit_matrices)
        elif len(circuit_matrices) > 1:
            self.ABCD = reduce(np.matmul, circuit_matrices)

    def sort_components(self):
        """
        Sorts components based on their node connections for consistent matrix multiplication order.
        """
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
    """
    Represents an individual component in the circuit with its type, node connections, and value.
    """

    def __init__(self, type, n1, n2, value):
        self.type = type
        self.n1 = n1
        self.n2 = n2
        self.value = value

    def get_abcd_matrix(self, s):
        """
        Calculates the ABCD matrix for the component based on its type and value.

        Args:
            s: The complex frequency.

        Returns:
            The 2x2 numpy array representing the ABCD matrix.
        """
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
    """
    Stores information about source, load, and frequency parameters for the circuit.
    """
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
        """
        Calculates various output parameters based on the circuit's ABCD matrix and termination values.

        Args:
            ABCD: The 2x2 numpy array representing the circuit's ABCD matrix.
        """
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
    """
    Represents an output parameter (e.g., Vin, Zout) with its name, value, unit, and formatting options.
    """
    def __init__(self, name, unit, magnitude, is_db):
        self.name = name  # Output parameter name, e.g., Vin, Vout, etc.
        self.value = None  # Value of the output parameter (calculated later)
        self.unit = unit  # Unit of the parameter, e.g., V (Volts), A (Amps), etc.
        self.magnitude = magnitude  # Magnitude prefix, e.g., k (kilo), m (milli), etc.
        self.is_db = is_db  # Boolean indicating if the output is in dB