# Tests/test_performance.py


import os
import glob
import threading

from main import main as main_function
import csv_writer

def test_performance():
    input_file_list = glob.glob('./User_files/*.net')
    output_file_list = [os.path.join('Tests', os.path.basename(file_path).replace('.net', '.csv')) for file_path in input_file_list]
    
    threads = []
    for input_file, output_file in zip(input_file_list, output_file_list):
        print(f"Input file: {input_file}")
        thread = threading.Thread(target=run_conversion, args=(input_file, output_file))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

def run_conversion(input_file, output_file):
    try:
        main_function(input_file, output_file)
        assert os.path.exists(output_file)
    except AssertionError:
        print(f"Output file was not created: {output_file}")
        with open(output_file, 'w', newline='', encoding='utf8') as csvfile:
            csv_writer.write_empty_csv(csvfile)
    except Exception as e:
        print(f"An error occurred processing {input_file}: {e}")
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == '__main__':
    test_performance()
