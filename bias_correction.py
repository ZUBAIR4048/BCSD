import os
import subprocess
from flask import Blueprint, render_template, request, jsonify, send_file, flash
from werkzeug.utils import secure_filename
import tempfile

bias_correction_bp = Blueprint('bias_correction', __name__)

OUTPUT_FOLDER = '/mnt'

@bias_correction_bp.route('/')
def bias_correction():
    variable = request.args.get('variable')
    if variable:
        return render_template('bias_now.html', variable=variable)
    else:
        return "Error: Variable not specified.", 400

@bias_correction_bp.route('/upload/<variable>', methods=['POST'])
def upload_files(variable):
    upload_path1 = upload_path2 = upload_path3 = None

    try:
        if 'file1' not in request.files or 'file2' not in request.files or 'file3' not in request.files:
            flash("Please upload all required files.", "error")
            return render_template('bias_now.html', variable=variable)

        file1 = request.files['file1']
        file2 = request.files['file2']
        file3 = request.files['file3']

        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path1 = os.path.join(temp_dir, secure_filename(file1.filename))
            upload_path2 = os.path.join(temp_dir, secure_filename(file2.filename))
            upload_path3 = os.path.join(temp_dir, secure_filename(file3.filename))

            file1.save(upload_path1)
            file2.save(upload_path2)
            file3.save(upload_path3)

            # Determine script path
            script_path = {
                'hurs': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_hurs.sh",
                'pr': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_pr.sh",
                'rlds': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_rlds.sh",
                'ps': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_ps.sh",
                'prsnratio': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_prsnratio.sh",
                'rsds': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_rsds.sh", 
                'sfcWind': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_sfcWind.sh", 
                'tas': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_tas.sh", 
                'tasrange': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_tasrange.sh",
                'tasskew': "/mnt/d/github/BCSD_Project/code/app/bias_correction/bias_tasskew.sh",            
            }.get(variable)

            if not script_path:
                flash("Unsupported variable.", "error")
                return render_template('bias_now.html', variable=variable)

            output_filename = f'{variable}_output.nc'
            output_file_path = os.path.join(OUTPUT_FOLDER, output_filename)

            command = ['bash', script_path, upload_path1, upload_path2, upload_path3, output_file_path]
            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                flash(f"Error processing files: {str(e)}", "error")
                return render_template('bias_now.html', variable=variable)

            if os.path.exists(output_file_path):
                return send_file(output_file_path, as_attachment=True, download_name=output_filename)
            else:
                flash("Result file not found.", "error")
                return render_template('bias_now.html', variable=variable)

    except FileNotFoundError as e:
        flash(f"File not found: {str(e)}", "error")
        return render_template('bias_now.html', variable=variable)

    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return render_template('bias_now.html', variable=variable)

    finally:
        # Clean up: Optionally delete the uploaded files and output after sending
        for path in [upload_path1, upload_path2, upload_path3]:
            if path and os.path.exists(path):
                os.remove(path)
