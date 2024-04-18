"""
This module defines the core classes for representing and analyzing electrical circuits:

- Circuit: Represents the overall circuit with components, terminations, and outputs.
- Component: Represents an individual circuit component (R, L, C, or G). 
- Terminations: Stores information about source and load terminations.
- Output: Represents an output parameter to be calculated (e.g., Vin, Zout).

The `Circuit` class provides methods for adding components, setting terminations,
and solving the circuit at specific frequencies using ABCD matrix analysis. 
It calculates output parameters like input/output impedance, voltage/current gains,
and power.

The `Component` class represents individual components and calculates their
corresponding ABCD matrices. 

The `Terminations` class stores information about the source and load and calculates
parameters like input/output impedance and input voltage/current.

The `Output` class represents individual output parameters and stores their 
calculated values and units.
"""

from functools import reduce
import numpy as np

def multiply_matrices(a, b):
    """
    Multiply two matrices a and b and return the result. Without using numpy.
    
    """
    
class Circuit:
    """
    Represents an electrical circuit with components, terminations, and output parameters.
    Provides methods for adding components, setting terminations, and solving the circuit using ABCD matrix analysis.
    """

    def __init__(self):
        """Initialize Circuit with empty component and output lists, and Termination object."""
        self.components = []
        self.outputs = []
        self.terminations = Terminations()
        self.frequency = None
        self.s = None
        self.ABCD = None

    def solve(self, f):
        """Analyze the circuit at a given frequency and calculate output parameters."""
        self.frequency = f
        self.s = 2j * np.pi * self.frequency
        self.resolve_matrix(self.s)
        self.terminations.calculate_outputs(self.ABCD)
        self.update_output_values()
        return self.outputs

    def add_component(self, component, n1, n2, value):
        """Add a component to the circuit."""
        self.components.append(Component(component, n1, n2, value))

    def set_termination(self, name, value):
        """Set a termination parameter for the circuit."""
        setattr(self.terminations, name, value)

    def add_output(self, name, unit, magnitude, is_db):
        """Add an output parameter to be calculated during circuit analysis."""
        self.outputs.append(Output(name, unit, magnitude, is_db))

    def resolve_matrix(self, s=0):
        """Calculate the overall ABCD matrix of the circuit for a given complex frequency."""
        circuit_matrices = [component.get_abcd_matrix(s) for component in self.components]
        self.ABCD = reduce(np.matmul, circuit_matrices, np.eye(2))

    def update_output_values(self):
        """Update output objects with calculated values based on terminations and ABCD matrix."""
        output_mappings = {'Zin': self.terminations.ZI, 'Zout': self.terminations.ZO, 'Vin': self.terminations.V1,
                           'Vout': self.terminations.VO, 'Iin': self.terminations.I1, 'Iout': self.terminations.IO,
                           'Pin': self.terminations.PI, 'Pout': self.terminations.PO, 'Av': self.terminations.AV,
                           'Ai': self.terminations.AI, 'Ap': self.terminations.AP}
        for output in self.outputs:
            value = output_mappings.get(output.name)
            if value is None:
                raise ValueError(f"Unknown output parameter: {output.name}")
            output.value = value
            
    def sort_components(self):
        """
        Sorts the components in the circuit based on their node connections to
        ensure consistent order for matrix multiplication when calculating the
        overall ABCD matrix.
        """
        def custom_sort_key(component):
            """
            Custom sorting key function that sorts components based on their node
            numbers, prioritizing connections to node 0 and then ordering by the
            lower node number.
            """
            # Extract n1 and n2, ignoring zeros.
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

        # Sort components using the custom key function.
        self.components = sorted(self.components, key=custom_sort_key)


class Component:
    """Represents an individual circuit component such as a resistor or capacitor."""

    def __init__(self, name, n1, n2, value):
        """Initialize Component with type, node connections, and value."""
        self.type = name
        self.n1 = n1
        self.n2 = n2
        self.value = value

    def get_abcd_matrix(self, s):
        """Calculate and return the ABCD matrix for the component based on its type and value."""
        is_shunt = self.n1 == 0 or self.n2 == 0
        match self.type:
            case 'R':
                Z = self.value
                if is_shunt:
                    abcd_matrix = [[1, 0], [1 / Z, 1]]
                else:
                    abcd_matrix = [[1, Z], [0, 1]]
            case 'L':
                sL = s * self.value
                if is_shunt:
                    abcd_matrix = [[1, 0], [1 / sL, 1]]
                else:
                    abcd_matrix = [[1, sL], [0, 1]]
            case 'C':
                sC = s * self.value
                if is_shunt:
                    abcd_matrix = [[1, 0], [sC, 1]]
                else:
                    abcd_matrix = [[1, 1 / sC], [0, 1]]
            case 'G':
                Y = self.value
                if is_shunt:
                    abcd_matrix = [[1, 0], [Y, 1]]
                else:
                    abcd_matrix = [[1, 1 / Y], [0, 1]]
        return np.array(abcd_matrix)


class Terminations:
    """Stores information about source and load terminations and calculates output parameters."""
    attributes = ['ZI', 'ZO', 'VO', 'IO', 'V1', 'V2', 'I1', 'I2', 'VT', 'RS', 'IN', 'GS', 'RL', 'AV', 'AI', 'AP', 'PI', 'PO']

    def __init__(self):
        """Initialize Terminations with attributes set to None."""
        for attr in self.attributes:
            setattr(self, attr, None)

    def calculate_outputs(self, ABCD):
        """Calculate output parameters based on the circuit's ABCD matrix and termination values."""
        A, B, C, D = ABCD.flatten()
        if self.RL:
            self.ZI = (A * self.RL + B) / (C * self.RL + D)
        else:
            raise ValueError("Load resistance (RL) must be provided.")
        if self.VT and self.RS:
            self.ZO = (D * self.RS + B) / (C * self.RS + A)
            self.I1 = self.VT / (self.RS + self.ZI)
            self.V1 = self.VT - self.I1 * self.RS
        elif self.IN and self.GS:
            self.ZO = (C + self.GS * A) / (D + self.GS * B)
            self.V1 = self.IN * (self.ZI / (1 + self.ZI * self.GS))
            self.I1 = self.IN - self.V1 * self.GS
        else:
            raise ValueError("Either Thevenin (VT and RS) or Norton (IN and GS) source parameters must be provided.")

        input_vector = np.array([[self.V1], [self.I1]])
        if np.linalg.det(ABCD) == 0:
            output_vector = np.array([[0], [0]])
        else:
            output_vector = np.dot(np.linalg.inv(ABCD), input_vector)
        
        self.V2, self.I2 = output_vector.flatten()
        self.AV = self.RL / (A * self.RL + B)
        self.AI = 1 / (C * self.RL + D)
        self.AP = self.AV * self.AI.conjugate()
        self.PI = self.V1 * self.I1.conjugate()
        self.PO = self.V2 * self.I2.conjugate()
        self.IO = self.I1 * self.AI
        self.VO = self.V1 * self.AV

class Output:
    """Represents an output parameter to be calculated during circuit analysis."""

    def __init__(self, name, unit, magnitude, is_db):
        """Initialize Output with name, unit, magnitude, and dB flag."""
        self.name = name
        self.value = None
        self.unit = unit
        self.magnitude = magnitude
        self.is_db = is_db
