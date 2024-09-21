from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import subprocess
import os

bias_bp = Blueprint('bias', __name__)

@bias_bp.route('/')
def index():
    return render_template('bias_now.html')

@bias_bp.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Get uploaded files
        file1 = request.files['file1']
        file2 = request.files['file2']
        file3 = request.files['file3']

        # Run the script and respond to the client
        return run_script(file1, file2, file3)
    except Exception as e:
        print(f"Error processing file upload: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

def run_script(file1, file2, file3):
    try:
        upload_path1 = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file1.filename))
        upload_path2 = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file2.filename))
        upload_path3 = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file3.filename))

        file1.save(upload_path1)
        file2.save(upload_path2)
        file3.save(upload_path3)

        # Output file path
        output_file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], 'tas_output.nc')

        # Run the bash script with uploaded file paths
        script_path = "/mnt/c/Users/HP/Desktop/isimip3basdCopy/code/application_example_tas-Copy.sh"
        wsl_script_path = '/'.join(script_path.split('\\'))
        subprocess.run(['bash', wsl_script_path, upload_path1, upload_path2, upload_path3, output_file_path], shell=False, check=True)
        if os.path.exists(output_file_path):
            return jsonify({'filename': output_file_path})
        else:
            return jsonify({'error': 'Result file not found'}), 500
    except Exception as e:
        print(f"Error processing file upload: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500
