# tests/test_circuit.py

import pytest
from circuit import Circuit, Component, Terminations, Output
import numpy as np

def test_add_component():
    circuit = Circuit()
    circuit.add_component('R', 1, 2, 100)
    component = circuit.components[0]
    assert component.type == 'R'
    assert component.n1 == 1
    assert component.n2 == 2
    assert component.value == 100

def test_resolve_matrix_simple_circuit():
    circuit = Circuit()
    circuit.add_component('R', 1, 2, 50)
    circuit.add_component('C', 2, 0, 1e-9)
    circuit.resolve_matrix(1j)
    expected_ABCD = np.array([[1.0, 50.0], [-1.0e-8j, 1.0]])
    assert np.allclose(circuit.ABCD, expected_ABCD)

def test_calculate_outputs_thevenin():
    terminations = Terminations()
    terminations.VT = 5
    terminations.RS = 50
    terminations.RL = 75
    ABCD = np.array([[1, 2], [3, 4]])  # Example ABCD matrix
    terminations.calculate_outputs(ABCD)
    assert terminations.Zin == pytest.approx(5.5)
    # Add more assertions for other output parameters

def test_calculate_outputs_norton():
    # Similar to Thevenin test but set Norton parameters

def test_output_value_formatting():
    output = Output("Vout", "V", "m", True)
    output.value = 1 + 2j
    assert output.value.real == pytest.approx(20*np.log10(abs(1+2j)))
    assert output.value.imag == pytest.approx(np.angle(1+2j)) 