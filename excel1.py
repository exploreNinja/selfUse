import os
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

def read_x_axis_labels(directory_path):
    with open(os.path.join(directory_path, 'x axis.txt'), 'r') as file:
        return sorted(file.read().splitlines(), key=lambda x: float(x))

def create_dataframe(directory_path, x_axis_labels):
    df = pd.DataFrame(index=x_axis_labels)
    for filename in sorted(os.listdir(directory_path)):
        if filename.endswith('.txt') and filename != 'x axis.txt':
            with open(os.path.join(directory_path, filename), 'r') as file:
                data = file.read().splitlines()
                if len(data) != len(x_axis_labels):
                    data += [np.nan] * (len(x_axis_labels) - len(data))
                df[filename.replace('.txt', '')] = pd.Series(data, index=x_axis_labels)
    df = df.sort_index().reindex(sorted(df.columns, key=lambda x: float(x)), axis=1)
    return df

def write_data_to_excel(df, output_directory_path):
    max_columns = 16384
    output_excel_file_base = os.path.join(output_directory_path, 'file_part_{}.xlsx')
    num_chunks = len(df.columns) // max_columns + 1
    for i in range(num_chunks):
        start_col = i * max_columns
        end_col = start_col + max_columns
        chunk = df.iloc[:, start_col:end_col]
        output_excel_file = output_excel_file_base.format(i)
        chunk.to_excel(output_excel_file)
        print(f'Data chunk {i} has been successfully written to {output_excel_file}')

@app.route('/process_files', methods=['POST'])
def process_files():
    data = request.get_json()
    directory_path = data.get('directory_path')
    output_directory_path = data.get('output_directory_path')

    if not directory_path or not output_directory_path:
        return jsonify({"error": "Both 'directory_path' and 'output_directory_path' are required"}), 400

    if not os.path.exists(directory_path):
        return jsonify({"error": f"Directory '{directory_path}' does not exist"}), 400

    os.makedirs(output_directory_path, exist_ok=True)

    try:
        x_axis_labels = read_x_axis_labels(directory_path)
        df = create_dataframe(directory_path, x_axis_labels)
        write_data_to_excel(df, output_directory_path)
        return jsonify({"message": "Files processed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
