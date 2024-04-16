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


class Circuit:
    """
    This class represents an electrical circuit with various components,
    terminations (source and load), and output parameters to be calculated. 
    It provides methods to add components, set terminations, and solve 
    the circuit for given frequencies using ABCD matrix analysis.
    """

    def __init__(self):
        self.components = []  # A list to store the circuit components (resistors, capacitors, inductors).
        self.outputs = []     # A list to store the desired output parameters (e.g., voltage gain, input impedance).
        self.terminations = Terminations()  # An object to hold information about the source and load.

        self.frequency = None  # The frequency at which the circuit is being analyzed.
        self.s = np.cdouble(0) # The complex frequency (s = jw) calculated from the frequency.

        self.ABCD = None  # The overall ABCD matrix of the circuit, calculated from component matrices. 

    def solve(self, f):
        """
        Analyzes the circuit at a given frequency and calculates the values for
        the specified output parameters.

        Args:
            f: The frequency in Hertz at which to analyze the circuit.

        Returns:
            A list of Output objects containing the calculated values for each output parameter.
        """
        self.frequency = f  # Store the analysis frequency.
        self.s = 2j * np.pi * self.frequency  # Calculate the complex frequency.
        self.resolve_matrix(self.s)  # Calculate the overall ABCD matrix of the circuit.
        self.terminations.calculate_outputs(self.ABCD)  # Calculate output parameters based on terminations and ABCD matrix.

        # Assign calculated values to each Output object based on its name.
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
        Adds a component (resistor, capacitor, inductor, or conductance) to the circuit.

        Args:
            component: The type of component ('R', 'L', 'C', or 'G').
            n1: The first node number the component is connected to.
            n2: The second node number the component is connected to.
            value: The value of the component (resistance, inductance, capacitance, or conductance).
        """
        self.components.append(Component(component, n1, n2, value))

    def set_termination(self, name, value):
        """
        Sets a termination parameter (source or load) for the circuit.

        Args:
            name: The name of the termination parameter (e.g., 'VT', 'RS', 'IN', 'RL').
            value: The value of the parameter (voltage, resistance, current, etc.).
        """
        setattr(self.terminations, name, value)

    def add_output(self, name, unit, magnitude, is_db):
        """
        Adds an output parameter to be calculated during circuit analysis.

        Args:
            name: The name of the output parameter (e.g., 'Vin', 'Zout').
            unit: The unit of the parameter (e.g., 'V', 'A', 'Ohm').
            magnitude: The magnitude prefix (e.g., 'k', 'm', '').
            is_db: Whether the output should be expressed in dB.
        """
        self.outputs.append(Output(name, unit, magnitude, is_db))

    def resolve_matrix(self, s=0):
        """
        Calculates the overall ABCD matrix of the circuit by multiplying the 
        individual ABCD matrices of the components in the correct order.

        Args:
            s: The complex frequency (optional, defaults to 0 for DC analysis).
        """
        # Get the ABCD matrix for each component at the specified complex frequency.
        circuit_matrices = [component.get_abcd_matrix(s) for component in self.components]  

        # Calculate the overall ABCD matrix based on the number of components.
        if len(circuit_matrices) == 0:  # No components
            self.ABCD = np.eye(2)  # Identity matrix
        elif len(circuit_matrices) == 1:  # One component 
            self.ABCD = np.array(circuit_matrices)  # Convert the single matrix to a NumPy array.
        elif len(circuit_matrices) > 1:  # Multiple components
            # Multiply component matrices in order using `functools.reduce` and `numpy.matmul`.
            self.ABCD = reduce(np.matmul, circuit_matrices)  

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
    """
    Represents a single component (resistor, capacitor, inductor, or conductance)
    in the circuit, storing its type, node connections, and value.
    """

    def __init__(self, type, n1, n2, value):
        self.type = type  # Type of component ('R', 'L', 'C', or 'G')
        self.n1 = n1    # First node number
        self.n2 = n2    # Second node number
        self.value = value  # Value of the component

    def get_abcd_matrix(self, s):
        """
        Calculates and returns the ABCD matrix for the component based on its type 
        and value at the specified complex frequency. 

        Args:
            s: The complex frequency (s = jw). 

        Returns:
            A 2x2 NumPy array representing the ABCD matrix for the component.
        """
        is_shunt = self.n1 == 0 or self.n2 == 0  # Check if the component is connected to ground (shunt). 

        match self.type:
            case 'R':  # Resistor 
                Z = self.value  # Impedance is equal to resistance.
                if is_shunt:
                    abcd_matrix = np.array([[1, 0], [1 / Z, 1]])
                else:
                    abcd_matrix = np.array([[1, Z], [0, 1]])
            case 'L':  # Inductor 
                sL = s * self.value  # Impedance is sL (s = jw, L = inductance)
                if is_shunt:
                    abcd_matrix = np.array([[1, 0], [1 / sL, 1]])
                else:
                    abcd_matrix = np.array([[1, sL], [0, 1]])
            case 'C':  # Capacitor
                sC = s * self.value  # Impedance is 1/sC
                if is_shunt:
                    abcd_matrix = np.array([[1, 0], [sC, 1]])
                else:
                    abcd_matrix = np.array([[1, 1 / sC], [0, 1]])
            case 'G':  # Conductance
                Y = self.value  # Admittance is equal to conductance.
                if is_shunt:
                    abcd_matrix = np.array([[1, 0], [Y, 1]])
                else:
                    abcd_matrix = np.array([[1, 1 / Y], [0, 1]])
            case _:  # Unknown component type
                raise ValueError(f"Unknown component type: {self.type}")
        return abcd_matrix


class Terminations:
    """
    This class stores information about the source and load terminations of 
    the circuit, including their values and types (Thevenin or Norton). It also 
    provides a method to calculate output parameters based on the circuit's
    ABCD matrix and the termination values. 
    """
    def __init__(self):
        self.ZI = None   # Input impedance seen by the source.
        self.ZO = None   # Output impedance seen by the load. 

        self.V1 = None   # Input voltage at node 1.
        self.V2 = None   # Output voltage at the load node.
        self.I1 = None   # Input current entering node 1.
        self.I2 = None   # Output current leaving the load node.

        # Parameters for Thevenin source representation:
        self.VT = None   # Thevenin equivalent voltage.
        self.RS = None   # Thevenin equivalent resistance.

        # Parameters for Norton source representation:
        self.IN = None   # Norton equivalent current. 
        self.GS = None   # Norton equivalent conductance (1/resistance). 

        self.RL = None   # Load resistance/impedance.

        self.Fstart = None  # Start frequency for linear frequency sweep.
        self.Fend = None    # End frequency for linear frequency sweep.

        self.LFstart = None # Start frequency for logarithmic frequency sweep.
        self.LFend = None   # End frequency for logarithmic frequency sweep.

        self.Nfreqs = None  # Number of frequency points for analysis.

        # Calculated output parameters:
        self.AV = None   # Voltage gain.
        self.AI = None   # Current gain.
        self.AP = None   # Power gain.

        self.PI = None   # Input power.
        self.PO = None   # Output power.

    def calculate_outputs(self, ABCD):
        """
        Calculates output parameters (Zin, Zout, Vin, Vout, Iin, Iout, Pin, Pout, Av, Ai, Ap)
        based on the circuit's ABCD matrix and the source and load termination values. 
        Handles both Thevenin and Norton source representations.

        Args:
            ABCD: The 2x2 NumPy array representing the circuit's ABCD matrix.
        """
        A, B, C, D = ABCD.flatten()  # Extract individual elements from the ABCD matrix.

        # Calculate input impedance based on load resistance.
        if self.RL:
            self.ZI = (A * self.RL + B) / (C * self.RL + D)  
        else:
            raise ValueError("Load resistance (RL) must be provided.")

        # Determine source type and calculate corresponding output impedance and input voltage/current.
        if self.VT and self.RS:  # Thevenin source
            self.ZO = (D * self.RS + B) / (C * self.RS + A)
            self.I1 = self.VT / (self.RS + self.ZI)
            self.V1 = self.VT - self.I1 * self.RS
        elif self.IN and self.GS:  # Norton source 
            self.ZO = (C + self.GS * A) / (D + self.GS * B)
            self.V1 = self.IN * (self.ZI / (1 + self.ZI * self.GS))
            self.I1 = self.IN - self.V1 * self.GS
        else:
            raise ValueError("Either Thevenin (VT and RS) or Norton (IN and GS) source parameters must be provided.")

        # Calculate output voltage and current using the inverse of the ABCD matrix.
        input_vector = np.array([[self.V1], [self.I1]])
        ABCD_inv = np.linalg.inv(ABCD)  # Calculate the inverse of the ABCD matrix.
        output_vector = ABCD_inv @ input_vector
        self.V2, self.I2 = output_vector.flatten()

        # Calculate voltage gain, current gain, and power gain. 
        self.AV = self.RL / (A * self.RL + B)
        self.AI = 1 / (C * self.RL + D)
        self.AP = self.AV * np.conj(self.AI) 

        # Calculate input and output power using complex conjugates.
        self.PI = self.V1 * np.conj(self.I1)  
        self.PO = self.V2 * np.conj(self.I2) 


class Output:
    """
    Represents an output parameter (e.g., 'Vin', 'Zout') to be calculated during
    circuit analysis, storing its name, value, unit, and formatting options 
    (whether to express in dB).
    """
    def __init__(self, name, unit, magnitude, is_db):
        self.name = name      # Name of the output parameter (e.g., Vin, Vout, etc.)
        self.value = None     # Value of the output parameter (calculated later) 
        self.unit = unit      # Unit of the parameter (e.g., V, A, Ohm)
        self.magnitude = magnitude  # Magnitude prefix (e.g., k, m, '')
        self.is_db = is_db    # Boolean indicating if the output is in dB 