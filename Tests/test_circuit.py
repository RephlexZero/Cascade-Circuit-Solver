# Tests/test_circuit.py

import pytest
from circuit import Circuit, Component, Output
import numpy as np

def test_add_component():
    circuit = Circuit()
    circuit.add_component('R', 1, 2, 100)
    component = circuit.components[0]
    assert component.type == 'R'
    assert component.n1 == 1
    assert component.n2 == 2
    assert component.value == 100
    
def test_sort_components():
    circuit = Circuit()
    circuit.add_component('B', 3, 2, None)
    circuit.add_component('C', 4, 5, None)
    circuit.add_component('A', 0, 1, None)
    circuit.add_component('C', 5, 4, None)
    circuit.add_component('D', 5, 6, None)
    circuit.add_component('D', 6, 5, None)
    circuit.add_component('A', 1, 0, None)
    
    circuit.sort_components()
    
    assert circuit.components[0].type == 'A'
    assert circuit.components[1].type == 'A'
    assert circuit.components[2].type == 'B'
    assert circuit.components[3].type == 'C'
    assert circuit.components[4].type == 'C'
    assert circuit.components[5].type == 'D'
    assert circuit.components[6].type == 'D'

def test_resolve_matrix_simple_circuit():
    circuit = Circuit()
    circuit.add_component('R', 1, 2, 50)
    circuit.add_component('C', 2, 0, 1e-9)
    circuit.add_component('L', 2, 3, 1e-3)
    abcd = np.matmul(circuit.components[0].get_abcd_matrix(1j),circuit.components[1].get_abcd_matrix(1j))
    abcd = np.matmul(abcd,circuit.components[2].get_abcd_matrix(1j))
    print(abcd)
    circuit.resolve_matrix(1j)
    expected_abcd = np.array([[ 1.+5.e-08j, 50.+1.e-03j],[ 0.+1.e-09j, 1.+0.e+00j]])
    assert np.allclose(circuit.abcd, expected_abcd)

def test_calculate_outputs_thevenin_norton():
    circuit = Circuit()
    circuit.abcd = np.array([[1, 2], [3, 4]])  # Example ABCD matrix
    t = circuit.terminations
    t["RL"] = 75
    
    t["VT"] = 5
    t["RS"] = 50
    circuit.calculate_outputs()
    thevanin_vout = t.get("Vout")
    thevanin_iout = t.get("Iout")
    
    t["IN"] = t["VT"] / t["RS"]
    t["GS"] = 1 / t["RS"]
    t["VT"], t["RS"] = None, None
    circuit.calculate_outputs()
    norton_vout = t.get("Vout")
    northon_iout = t.get("Iout")

    assert thevanin_vout ==  pytest.approx(norton_vout)
    assert thevanin_iout ==  pytest.approx(northon_iout)