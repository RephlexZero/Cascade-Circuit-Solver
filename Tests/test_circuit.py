# Tests/test_circuit.py

import pytest
from circuit import Circuit
import numpy as np

@pytest.mark.parametrize("component_type, n1, n2, value", [
    ('R', 1, 2, 100),
    ('C', 2, 3, 1e-6),
    ('L', 4, 5, 1e-3)
])
def test_add_component(component_type, n1, n2, value):
    circuit = Circuit()
    circuit.add_component(component_type, n1, n2, value)
    component = circuit.components[0]
    assert component.type == component_type
    assert component.n1 == n1
    assert component.n2 == n2
    assert component.value == value

@pytest.mark.parametrize("inputs, expected", [
    ([
        ('B', 3, 2, None),
        ('C', 4, 5, None),
        ('A', 0, 1, None),
        ('C', 5, 4, None),
        ('D', 5, 6, None),
        ('D', 6, 5, None),
        ('A', 1, 0, None)
     ],
     ['A', 'A', 'B', 'C', 'C', 'D', 'D'])
])
def test_sort_components(inputs, expected):
    circuit = Circuit()
    for inp in inputs:
        circuit.add_component(*inp)
    circuit.sort_components()
    assert [comp.type for comp in circuit.components] == expected

def test_resolve_matrix_simple_circuit():
    circuit = Circuit()
    circuit.add_component('R', 1, 2, 50)
    circuit.add_component('C', 2, 0, 1e-9)
    circuit.add_component('L', 2, 3, 1e-3)

    # Calculate combined ABCD matrix manually
    frequency = 1j  # Imaginary unit for jω
    abcd = np.eye(2)  # Start with the identity matrix
    for comp in circuit.components:
        abcd = np.matmul(abcd, comp.get_abcd_matrix(frequency))

    # Compute expected matrix and compare
    expected_abcd = np.array([[1.+5.e-08j, 50.+1.e-03j], [0.+1.e-09j, 1.+0.e+00j]])
    assert np.allclose(abcd, expected_abcd), "ABCD matrices do not match"

@pytest.mark.parametrize("abcd_matrix, vt, rs, rl", [
    (np.array([[1, 2], [3, 4]]), 5, 50, 75),
])
def test_calculate_outputs_thevenin_norton(abcd_matrix, vt, rs, rl):
    circuit = Circuit()
    circuit.abcd = abcd_matrix
    t = circuit.terminations
    t["RL"] = rl
    t["VT"] = vt
    t["RS"] = rs
    circuit.calculate_outputs()
    thevanin_vout = t.get("Vout")
    thevanin_iout = t.get("Iout")

    t["IN"] = t["VT"] / t["RS"]
    t["GS"] = 1 / t["RS"]
    t["VT"], t["RS"] = None, None
    circuit.calculate_outputs()
    norton_vout = t.get("Vout")
    northon_iout = t.get("Iout")

    assert thevanin_vout == pytest.approx(norton_vout)
    assert thevanin_iout == pytest.approx(northon_iout)
