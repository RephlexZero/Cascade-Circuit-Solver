# Tests/test_net_parser.py

import pytest
from net_parser import parse_net_file_to_circuit, MalformedInputError, process_circuit_line, process_terms_line, process_output_line
from circuit import Circuit, Component
from math import isclose

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
    assert circuit.terminations["LFstart"] == 10.0
    assert circuit.terminations["LFend"] == 10e+6
    assert circuit.terminations["Nfreqs"] == 10
    assert circuit.terminations["VT"] == 5
    assert circuit.terminations["RS"] == 50
    assert circuit.terminations["RL"] == 75
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

def test_process_incorrect_circuit_lines():
    circuit = Circuit()
    lines = [
        "n1=1 n3=2 R=8.55u",
        "n1=1 n2=3 R=8.55u",
        "n1=1 n2=2 T=8.55u",
        "n1=1 n2=2 R=k8.55u"
    ]

    for line in lines:
        with pytest.raises(MalformedInputError):
            process_circuit_line(line, circuit)
   
def test_process_correct_circuit_lines():
    circuit = Circuit()
    lines = [
        "n1=1 n2=2 R=8.55",
        "n1=3 n2=4 L=0.1 m",
        "n1=5 n2=6 C=100 n",
        "n1=7 n2=8 G=0.01",
        "n1=9 n2=10 R=10 k",
        "L=0.1 m n2=11 n1=12",
        "L  =     1   m    n2   = 13    n1 =  14"
    ]

    for line in lines:
        process_circuit_line(line, circuit)
        
    component = circuit.components[0]
    assert component.type == 'R'
    assert component.n1 == 1
    assert component.n2 == 2
    assert isclose(component.value, 8.55)
    component = circuit.components[1]
    assert component.type == 'L'
    assert component.n1 == 3
    assert component.n2 == 4
    assert isclose(component.value, 0.1e-3)
    component = circuit.components[2]
    assert component.type == 'C'
    assert component.n1 == 5
    assert component.n2 == 6
    assert isclose(component.value, 100e-9)
    component = circuit.components[3]
    assert component.type == 'G'
    assert component.n1 == 7
    assert component.n2 == 8
    assert isclose(component.value, 0.01)
    component = circuit.components[4]
    assert component.type == 'R'
    assert component.n1 == 9
    assert component.n2 == 10
    assert isclose(component.value, 10e3)
    component = circuit.components[5]
    assert component.type == 'L'
    assert component.n1 == 12
    assert component.n2 == 11
    assert isclose(component.value, 0.1e-3)
    component = circuit.components[6]
    assert component.type == 'L'
    assert component.n1 == 14
    assert component.n2 == 13
    assert isclose(component.value, 1e-3)

def test_process_correct_terms_lines():
    circuit = Circuit()
    lines = [
        "LFstart=10.0 LFend=10 Nfreqs=10 VT=5 RS=50 RL=75",
        "LFstart=10 LFend=10E-3 Nfreqs  =10E3 VT   = 5  RS  =50 RL=75"
    ]

    for line in lines:
        process_terms_line(line, circuit)

# Incorrect terms lines are not tested because the function does not raise any exceptions for them,
# it ignores them if possible, otherwise they are caught higher up in calculations as invalid terms
# will be missing.

def test_process_correct_output_lines():
    circuit = Circuit()
    lines = [
        "Vin mV",
        "Vin dBmV",
        "Vout V",
        "Vout dBV",
        "Iin uA"
    ]

    for line in lines:
        process_output_line(line, circuit)

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
    
def test_process_incorrect_output_lines():
    circuit = Circuit()
    lines = [
        "Vin mV dB",
        "Vin dBmV V",
        "Vout V dB",
        "Vout dBV A",
        "Iin uA V"
    ]

    for line in lines:
        with pytest.raises(MalformedInputError):
            process_output_line(line, circuit)