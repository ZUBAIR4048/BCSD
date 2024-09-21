import os
import subprocess
from flask import Blueprint, render_template, request, flash, send_file
from werkzeug.utils import secure_filename
import tempfile

statistical_downscaling_bp = Blueprint('statistical_downscaling', __name__)

OUTPUT_FOLDER = '/mnt'

@statistical_downscaling_bp.route('/')
def statistical_downscaling():
    variable = request.args.get('variable')
    if variable:
        return render_template('stats2.html', variable=variable)
    else:
        return "Error: Variable not specified.", 400

@statistical_downscaling_bp.route('/upload/<variable>', methods=['POST'])
def upload_files(variable):
    print(f"Uploading files for variable: {variable}")
    upload_path1 = upload_path2 = None

    try:
        if 'file1' not in request.files or 'file2' not in request.files:
            flash("Please upload both required files.", "error")
            return render_template('stats2.html', variable=variable)

        file1 = request.files['file1']
        file2 = request.files['file2']

        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path1 = os.path.join(temp_dir, secure_filename(file1.filename))
            upload_path2 = os.path.join(temp_dir, secure_filename(file2.filename))

            file1.save(upload_path1)
            file2.save(upload_path2)

            print(f"File 1 saved to: {upload_path1}")
            print(f"File 2 saved to: {upload_path2}")

            script_path = {
                'hurs': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_hurs.sh",
                'pr': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_pr.sh",
                'rlds': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_rlds.sh",
                'ps': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_ps.sh",
                'prsnratio': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_prsnratio.sh",
                'rsds': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_rsds.sh", 
                'sfcWind': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_sfcWind.sh", 
                'tas': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_tas.sh", 
                'tasrange': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_tasrange.sh",
                'tasskew': "/mnt/d/github/BCSD_Project/code/app/statistical_downscaling/statistical_tasskew.sh",
            }.get(variable)


            print(f"Script path resolved to: {script_path}")

            if not script_path or not os.path.exists(script_path):
                print("Error: Script not found or variable unsupported.")
                flash("Unsupported variable or script not found.", "error")
                return render_template('stats2.html', variable=variable)

            output_filename = f'{variable}_downscaled_output.nc'
            output_file_path = os.path.join(OUTPUT_FOLDER, output_filename)

            command = ['bash', script_path, upload_path1, upload_path2, output_file_path]
            try:
                print(f"Running command: {command}")
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error processing files: {str(e)}")
                flash(f"Error processing files: {str(e)}", "error")
                return render_template('stats2.html', variable=variable)

            if os.path.exists(output_file_path):
                return send_file(output_file_path, as_attachment=True, download_name=output_filename)
            else:
                flash("Result file not found.", "error")
                return render_template('stats2.html', variable=variable)

    except FileNotFoundError as e:
        flash(f"File not found: {str(e)}", "error")
        return render_template('stats2.html', variable=variable)

    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return render_template('stats2.html', variable=variable)

    finally:
        for path in [upload_path1, upload_path2]:
            if path and os.path.exists(path):
                os.remove(path)
