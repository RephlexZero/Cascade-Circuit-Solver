# Tests/test_csv_writer.py

from csv_writer import write_header, write_data_line
from circuit import Circuit, Output
import io

def test_write_header():
    circuit = Circuit()
    circuit.outputs = [Output("Vout", "V", "", False),
                       Output("Iin", "A", "u", True)]
    csvfile = io.StringIO()
    write_header(circuit, csvfile)
    header = csvfile.getvalue().replace(" ", "").split("\n")
    assert header[0].strip().split(",") == ["Freq", "Re(Vout)", "Im(Vout)", "|Iin|", "/_Iin"]
    assert header[1].strip().split(",") == ["Hz", "V", "V", "dBuA", "Rads"]

def test_write_data_line():
    circuit = Circuit()
    frequency = 1e6
    circuit.outputs = [Output("Vout", "V", "", False),
                       Output("Iin", "A", "u", True)]
    circuit.outputs[0].value = 1 + 2j
    circuit.outputs[1].value = 3 - 4j
    csvfile = io.StringIO()
    write_data_line(circuit, csvfile, frequency)
    # Remove all white spaces and split by comma
    data_row = csvfile.getvalue().replace(" ", "").strip().split(",")
    # Assert data row format for both real/imag and dB/phase
    assert data_row == ["1.000e+06", "1.000e+00", "2.000e+00", "1.398e+07", "-9.273e-01",""]
    # Include the extra empty field to match error in model files