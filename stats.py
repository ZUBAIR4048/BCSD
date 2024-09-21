from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import subprocess
import os

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/')
def index():
    return render_template('stats2.html')

@stats_bp.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Get uploaded files
        file1 = request.files['file1']
        file2 = request.files['file2']

        # Run the script and respond to the client
        return run_script(file1, file2)
    except Exception as e:
        print(f"Error processing file upload: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

def run_script(file1, file2):
    try:
        upload_path1 = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file1.filename))
        upload_path2 = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file2.filename))

        file1.save(upload_path1)
        file2.save(upload_path2)

        # Output file path
        output_file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], 'output.nc')

        # Run the bash script with uploaded file paths
        script_path = "/mnt/c/Users/HP/Desktop/isimip3basdCopy/code/statistical_hurs.sh"
        wsl_script_path = '/'.join(script_path.split('\\'))
        subprocess.run(['bash', wsl_script_path, upload_path1, upload_path2, output_file_path], shell=False, check=True)
        if os.path.exists(output_file_path):
            return jsonify({'filename': output_file_path})
        else:
            return jsonify({'error': 'Result file not found'}), 500
    except Exception as e:
        print(f"Error processing file upload: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500
