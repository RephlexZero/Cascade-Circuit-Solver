import cProfile
import glob
import os
import main

input_file_list = glob.glob('./User_files/*.net')
# Make another list of the same files, but with the .net extension replaced with .csv
output_file_list = [file_path.replace('.net', '.csv') for file_path in input_file_list]
# Start a thread for each file in the list
for input_file, output_file in zip(input_file_list, output_file_list):
    # Start a new thread to run the main function with the input and output file paths
    try:
        main.main(input_file, output_file)
        # cProfile.run('main.main(input_file, output_file)', f'{os.path.basename(input_file).replace(".net", ".prof")}')
    except Exception as e:
        import csv_writer
        csv_writer.write_empty_csv(output_file)