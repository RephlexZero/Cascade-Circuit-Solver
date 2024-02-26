import numpy as np
from functools import reduce

# Example ABCD matrix functions for each component type
def resistor_abcd(R):
    return np.array([[1, R], [0, 1]])

def capacitor_abcd(C, s):
    if s == 0:
        return np.array([[1, np.inf], [0, 1]])
    else:
        return np.array([[1, 1/(s*C)], [0, 1]])

def inductor_abcd(L, s):
    return np.array([[1, 0], [s*L, 1]])

# s = 1i*2*np.pi*f, where f is the frequency in Hz

# Function to get ABCD matrix for a component
def get_abcd_matrix(component, s=0):
    type = component.type
    value = component.value
    abcd = None

    match type:
        case 'R':
            abcd = resistor_abcd(value)
        case 'C':
            abcd = capacitor_abcd(value, s)
        case 'L':
            abcd = inductor_abcd(value, s)
        case _:
            raise ValueError("Unknown component type")
    
    # Transpose if connected to ground (node 0)
    if 0 in [component.n1, component.n2]:
        abcd = np.transpose(abcd)
    
    return abcd

# Function to multiply matrices left to right
def multiply_matrices(matrices):
    # Use reduce to consecutively multiply matrices from left to right
    # np.dot is used for matrix multiplication
    result_matrix = reduce(np.dot, matrices)
    return result_matrix