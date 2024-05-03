# Author: Jake Stewart
# Email: js3910@bath.ac.uk
# License: MIT
import os
import glob
import cProfile

from main import main as main_function
import csv_writer


def test_performance():
    input_file_list = glob.glob('./User_files/*.net')
    output_file_list = [os.path.join('Tests', os.path.basename(file_path).replace('.net', '.csv')) for file_path in input_file_list]
    profiles_dir = './Tests/Profiles'
    os.makedirs(profiles_dir, exist_ok=True)

    for input_file, output_file in zip(input_file_list, output_file_list):
        print(f"Input file: {input_file}")
        profile_output = os.path.join(profiles_dir, f"{os.path.basename(input_file)}.prof")
        run_conversion_with_profile(input_file, output_file, profile_output)


def run_conversion_with_profile(input_file, output_file, profile_output):
    profiler = cProfile.Profile()
    profiler.enable()
    run_conversion(input_file, output_file)
    profiler.disable()
    profiler.dump_stats(profile_output)


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

