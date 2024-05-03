# Author: Jake Stewart
# Email: js3910@bath.ac.uk
# License: MIT
import pytest
from net_parser import MalformedInputError
from net_parser import process_circuit_line, process_output_line, process_terms_line
from circuit import Circuit

@pytest.fixture
def sample_circuit():
    """Fixture to create a basic circuit for testing."""
    return Circuit()

@pytest.mark.parametrize("line, expected_exception", [
    ("n1=1 n3=2 R=8.55u", MalformedInputError),
    ("n1=1 n2=3 R=8.55u", MalformedInputError),  # Assuming this is actually valid
    ("n1=1 n2=2 T=8.55u", MalformedInputError),
    ("n1=1 n2=2 R=k8.55u", MalformedInputError),
    ("n1=1 n2=2 R=k8.55uu", MalformedInputError),
    ("n1=1 n2=2 R=8.55K", MalformedInputError),
    ("n1=1 n2=2 R=8.55kM", MalformedInputError),
    ("n1=1 n2=2 R=8E10k", None),
    ("n1=1 n2=2 R=8.5E-50", None),
    ("n1  = 1 n2 =  2 R = 8.5E-50", None)
])
def test_process_circuit_lines(sample_circuit, line, expected_exception):
    if expected_exception:
        with pytest.raises(expected_exception):
            process_circuit_line(line, sample_circuit)
    else:
        process_circuit_line(line, sample_circuit)

@pytest.mark.parametrize("line, name, unit, magnitude, is_db", [
    ("Vin mV", "Vin", "V", "m", False),
    ("Vin dBmV", "Vin", "V", "m", True),
    ("Vout V", "Vout", "V", "", False),
    ("Vout dBV", "Vout", "V", "", True),
    ("Iin uA", "Iin", "A", "u", False)
])
def test_process_correct_output_lines(sample_circuit, line, name, unit, magnitude, is_db):
    process_output_line(line, sample_circuit)
    output = sample_circuit.outputs[-1]  # Assuming the line adds to outputs
    assert output.name == name
    assert output.unit == unit
    assert output.magnitude == magnitude
    assert output.is_db == is_db

@pytest.mark.parametrize("line", [
    ("Vin Vm"),
    ("Vin mdBV"),
    ("Vouts V"),
    ("Vout dBVs"),
    ("uA Iin")
])
def test_process_incorrect_output_lines(sample_circuit, line):
    with pytest.raises(MalformedInputError):
        process_output_line(line, sample_circuit)

@pytest.mark.parametrize("line, expected_values", [
    ("LFstart=10.0 LFend=10 Nfreqs=10 VT=5 RS=50 RL=75",
     {'LFstart': 10.0, 'LFend': 10, 'Nfreqs': 10, 'VT': 5, 'RS': 50, 'RL': 75}),
    ("LFstart=10 LFend=10E-3 Nfreqs=10E3 VT=5 RS=50 RL=75",
     {'LFstart': 10, 'LFend': 0.01, 'Nfreqs': 10000, 'VT': 5, 'RS': 50, 'RL': 75}),
])
def test_process_correct_terms_lines(sample_circuit, line, expected_values):
    process_terms_line(line, sample_circuit)
    print(sample_circuit.terminations)
    for key, value in expected_values.items():
        assert sample_circuit.terminations.get(key) == value

@pytest.mark.parametrize("line", [
    "LFstart=10.0 LFend=NaN Nfreqs=ten VT=5 RS=fifty RL=seventy-five",
    "LFstart==10.0 LFend=10 Nfreqs==10 VT==5 RS==50 RL==75",
    "StartLF=10 EndLF=10 Nfreqs=10 VT=5 RS=50 RL=75",
    "StartLF=10 EndLF=10 Nfreqs=10 VT=5 RS=50 RL=75 hi"
])
def test_process_incorrect_terms_lines(sample_circuit, line):
    with pytest.raises(MalformedInputError):
        process_terms_line(line, sample_circuit)