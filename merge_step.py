from flask import Blueprint, request, jsonify, render_template
import os, glob, logging, subprocess, time

merge_bp = Blueprint('merge', __name__, template_folder='templates')

UPLOAD_FOLDER = 'uploads_mergetime'
OUTPUT_FOLDER = 'merged_output'

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Created directory: {directory}")
    else:
        logging.info(f"Directory already exists: {directory}")

@merge_bp.route('/')
def index():
    return render_template('merge.html')

@merge_bp.route('/upload', methods=['POST'])
def upload():
    try:
        ensure_directory(os.path.join(UPLOAD_FOLDER, 'historical'))
        ensure_directory(os.path.join(UPLOAD_FOLDER, 'scenarios'))
        ensure_directory(OUTPUT_FOLDER)

        files1 = request.files.getlist('files1[]')
        files2 = request.files.getlist('files2[]')

        for file in files1:
            if file:
                file_path = os.path.join(UPLOAD_FOLDER, 'historical', file.filename)
                file.save(file_path)
                logging.info(f"Saved historical file: {file_path}")
        for file in files2:
            if file:
                file_path = os.path.join(UPLOAD_FOLDER, 'scenarios', file.filename)
                file.save(file_path)
                logging.info(f"Saved scenario file: {file_path}")

        historical_files = glob.glob(os.path.join(UPLOAD_FOLDER, 'historical', "*.nc4"))
        scenario_files = glob.glob(os.path.join(UPLOAD_FOLDER, 'scenarios', "*.nc4"))

        if historical_files and scenario_files:
            all_files = historical_files + scenario_files
            unique_id = str(int(time.time()))  # Unique identifier based on timestamp
            output_file_path = os.path.join(OUTPUT_FOLDER, f'merged_output_{unique_id}.nc4')
            cdo_command = ["cdo", "mergetime"] + all_files + [output_file_path]
            logging.info(f"Running command: {' '.join(cdo_command)}")

            result = subprocess.run(cdo_command, capture_output=True, text=True)
            logging.info(f"CDO command output: {result.stdout}")
            if result.stderr:
                logging.error(f"CDO command error: {result.stderr}")

            if os.path.exists(output_file_path):
                logging.info(f"Output file created: {output_file_path}")
            else:
                logging.error(f"Output file not created: {output_file_path}")

        output_dir_contents = os.listdir(OUTPUT_FOLDER)
        logging.info(f"Contents of the output directory: {output_dir_contents}")

        return jsonify({'message': 'Files uploaded and processed successfully!'})
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'message': f"An error occurred: {str(e)}"}), 500
