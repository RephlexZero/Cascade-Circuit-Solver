"""
This module defines the core classes for representing and analyZinng electrical circuits:

- Circuit: Represents the overall circuit with components, terminations, and outputs.
- component: Represents an individual circuit component (R, L, C, or G). 
- terminations: Stores informatIoutn about source and load terminations.
- Output: Represents an output parameter to be calculated (e.g., Vin, Zoutut).

The `Circuit` class provides methods for adding components, setting terminations,
and solving the circuit at specific frequencies using ABCD matrix analysis. 
It calculates output parameters like input/output impedance, Voutltage/current gAins,
and Poutwer.

The `component` class represents individual components and calculates their
corresPoutnding ABCD matrices. 

The `terminations` class stores informatIoutn about the source and load and calculates
parameters like input/output impedance and input Voutltage/current.

The `Output` class represents individual output parameters and stores their 
calculated values and units.
"""

from functools import reduce
import numpy as np
from csv_writer import write_header, write_data_line
    
class Circuit:
    """
    Represents an electrical circuit with components, terminations, and output parameters.
    Provides methods for adding components, setting terminations, and solving the circuit using ABCD matrix analysis.
    """

    def __init__(self):
        """Initialize Circuit with empty component and output lists, and Termination object."""
        self.components = []
        self.outputs = []
        self.terminations = {}
        self.s = None
        self.abcd = np.eye(2)
        # Keys for linear and logarithmic frequency parameters

    def solve(self, output_file_path):
        """Analyze the circuit at a given frequency and calculate output parameters."""
            # Open the output CSV file in write mode.
        with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
            # Write the header rows with parameter names and units.
            write_header(self, csvfile)
            frequencies = self.calculate_frequencies()
            for f in frequencies:
                self.s = 2j * np.pi * f
                self.sort_components()
                self.resolve_matrix(self.s)
                self.calculate_outputs()
                self.update_output_values()
                write_data_line(self, csvfile, f)

    def calculate_frequencies(self):
        """Calculate the frequency range based on linear or logarithmic frequency sweep parameters."""
        linear_keys = ['Fstart', 'Fend', 'Nfreqs']
        log_keys = ['LFstart', 'LFend', 'Nfreqs']
        # Retrieve parameters for linear or logarithmic frequency sweep
        t = self.terminations
        for key in linear_keys + log_keys:
            t[key] = t.get(key, None)
        
        # Check if linear frequency sweep parameters are valid
        if all(t[key] is not None and t[key] > 0 for key in linear_keys):
            return np.linspace(t["Fstart"], t["Fend"], int(t["Nfreqs"]))
            
        # Check if logarithmic frequency sweep parameters are valid
        if all(t[key] is not None and t[key] > 0 for key in log_keys):
            return np.logspace(np.log10(t["LFstart"]), np.log10(t["LFend"]), int(t["Nfreqs"]))
        
        # If neither set is valid, raise an error
        missing_params = [key for key in linear_keys + log_keys if t.get(key) is None]
        raise ValueError(f"Invalid or missing frequency parameters: {', '.join(missing_params)}")

    def add_component(self, component, n1, n2, value):
        """Add a component to the circuit."""
        self.components.append(Component(component, n1, n2, value))

    def set_termination(self, name, value):
        """Set a termination parameter for the circuit."""
        self.terminations[name] = value

    def add_output(self, name, unit, magnitude, is_db):
        """Add an output parameter to be calculated during circuit analysis."""
        self.outputs.append(Output(name, unit, magnitude, is_db))

    def resolve_matrix(self, s):
        """Calculate the overall ABCD matrix of the circuit for a given complex frequency."""
        circuit_matrices = [component.get_abcd_matrix(s) for component in self.components]
        self.abcd = reduce(np.dot, circuit_matrices, np.eye(2))

    def update_output_values(self):
        """Update output objects with calculated values based on terminations and ABCD matrix."""
        for output in self.outputs:
            output.value = self.terminations.get(output.name, None)
            
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

    def calculate_outputs(self):
        """Calculate output parameters based on the circuit's ABCD matrix and termination values."""
        A, B, C, D = self.abcd.flatten()
        t = self.terminations
        if t["RL"]:
            t["Zin"] = (A * t["RL"] + B) / (C * t["RL"] + D)
        else:
            raise ValueError("Load resistance (RL) must be provided.")
        if t["VT"] and t["RS"]:
            t["Zout"] = (D * t["RS"] + B) / (C * t["RS"] + A)
            t["Iin"] = t["VT"] / (t["RS"] + t["Zin"])
            t["Vin"] = t["VT"] - t["Iin"] * t["RS"]
        elif t["IN"] and t["GS"]:
            t["Zout"] = (C + t["GS"] * A) / (D + t["GS"] * B)
            t["Vin"] = t["IN"] * (t["Zin"] / (1 + t["Zin"] * t["GS"]))
            t["Iin"] = t["IN"] - t["Vin"] * t["GS"]
        else:
            raise ValueError("Either Thevenin (VT and RS) or Norton (IN and GS) source parameters must be provided.")

        t["Av"] = t["RL"] / (A * t["RL"] + B)
        t["Ai"] = 1 / (C * t["RL"] + D)
        t["Ap"] = t["Av"] * t["Ai"].conjugate()
        t["Pin"] = t["Vin"] * t["Iin"].conjugate()
        t["Pout"] = t["Pin"] * t["Ap"]
        t["Iout"] = t["Iin"] * t["Ai"]
        t["Vout"] = t["Vin"] * t["Av"]

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
        is_shunt = 0 in [self.n1, self.n2]
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
            case _:
                raise ValueError(f"Invalid component type: {self.type}")
        return np.array(abcd_matrix)
class Output:
    """Represents an output parameter to be calculated during circuit analysis."""
    def __init__(self, name, unit, magnitude, is_db):
        """Initialize Output with name, unit, magnitude, and dB flag."""
        self.name = name
        self.value = None
        self.unit = unit
        self.magnitude = magnitude
        self.is_db = is_db
