# tests/test_net_parser.py

from typing import assert_type
import pytest
from net_parser import parse_net_file_to_circuit, MalformedInputError, process_circuit_line
from circuit import Circuit, Component

def test_parse_valid_net_file():
    circuit = parse_net_file_to_circuit("Tests/Ext_mdB_a_Test_Circuit_1.net")
    assert len(circuit.components) == 10  # Example assertion - adapt to your valid.net
    assert isinstance(circuit.components[0], Component)
    # n1=1 n2=2 R=8.55
    component = circuit.components[0]
    assert component.type == 'R'
    assert component.n1 == 1
    assert component.n2 == 2
    assert component.value == 8.55
    # n1=4 n2=5 C=637 n
    component = circuit.components[6]
    assert component.type == 'C'
    assert component.n1 == 4
    assert component.n2 == 5
    assert component.value == 637e-9
    # LFstart=10.0 LFend=10e+6 Nfreqs=10 VT=5 RS=50 RL=75
    assert circuit.terminations.LFstart == 10.0
    assert circuit.terminations.LFend == 10e+6
    assert circuit.terminations.Nfreqs == 10
    assert circuit.terminations.VT == 5
    assert circuit.terminations.RS == 50
    assert circuit.terminations.RL == 75
    # Vin mV, Vin dBmV, Vout V, Vout dBV, Iin uA
    output = circuit.outputs[0]
    assert output.name == "Vin"
    assert output.unit == "V"
    assert output.magnitude == "m"
    assert output.is_db is False
    output = circuit.outputs[1]
    assert output.name == "Vin"
    assert output.unit == "V"
    assert output.magnitude == "m"
    assert output.is_db is True
    output = circuit.outputs[2]
    assert output.name == "Vout"
    assert output.unit == "V"
    assert output.magnitude == ""
    assert output.is_db is False
    output = circuit.outputs[3]
    assert output.name == "Vout"
    assert output.unit == "V"
    assert output.magnitude == ""
    assert output.is_db is True
    output = circuit.outputs[4]
    assert output.name == "Iin"
    assert output.unit == "A"
    assert output.magnitude == "u"
    assert output.is_db is False

def test_parse_invalid_circuit_line():
    with pytest.raises(MalformedInputError, match="Invalid circuit line"):
        process_circuit_line("")

def test_parse_invalid_terms_line():
    with pytest.raises(MalformedInputError, match="Invalid terms line"):
        parse_net_file_to_circuit("tests/data/invalid_terms.net")

def test_parse_invalid_output_line():
    with pytest.raises(MalformedInputError, match="Invalid output line"):
        parse_net_file_to_circuit("tests/data/invalid_output.net")

def test_parse_missing_section():
    with pytest.raises(MalformedInputError, match="section not properly formatted"):
        parse_net_file_to_circuit("tests/data/missing_section.net")