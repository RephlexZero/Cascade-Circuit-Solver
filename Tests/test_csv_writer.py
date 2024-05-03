# Author: Jake Stewart
# Email: js3910@bath.ac.uk
# License: MIT
import io
from csv_writer import write_header, write_data_line, write_empty_csv
from circuit import Circuit


def test_write_header():
    # Setup: create a Circuit object with specific outputs
    circuit = Circuit()
    circuit.outputs = [Circuit.Output("Vout", "V", "", False),
                       Circuit.Output("Iin", "A", "u", True)]

    # Action: simulate writing to a CSV file
    csvfile = io.StringIO()
    write_header(circuit, csvfile)

    # Fetch the written data, remove spaces, and split into lines
    header = csvfile.getvalue().replace(" ", "").split("\n")
    
    # Assertions: check the structure and content of the CSV header
    assert header[0].strip().split(",") == ["Freq", "Re(Vout)", "Im(Vout)", "|Iin|", "/_Iin"]
    assert header[1].strip().split(",") == ["Hz", "V", "V", "dBuA", "Rads"]

    # Setup: create a Circuit with outputs containing complex values
    circuit = Circuit()
    frequency = 1e6
    circuit.outputs = [Circuit.Output("Vout", "V", "", False),
                       Circuit.Output("Iin", "A", "u", True)]
    circuit.outputs[0].value = 1 + 2j
    circuit.outputs[1].value = 3 - 4j

    # Action: simulate writing a data line to a CSV
    csvfile = io.StringIO()
    write_data_line(circuit, csvfile, frequency)
    
    # Fetch the written data, remove spaces, and split by comma
    data_row = csvfile.getvalue().replace(" ", "").strip().split(",")

    # Assertions: validate the data format and content
    assert data_row == ["1.000e+06", "1.000e+00", "2.000e+00", "1.340e+02", "-9.273e-01",""]
    # Note: the extra empty field matches a potential formatting error in model files


def test_write_empty_csv():
    # Setup: simulate an empty CSV file
    csvfile = io.StringIO()
    write_empty_csv(csvfile)
    
    # Fetch the written data
    data_row = csvfile.getvalue()
    
    # Assertion: check that the file remains empty after the operation
    assert data_row == ""

