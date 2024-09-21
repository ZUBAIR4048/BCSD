from flask import Blueprint, request, render_template, redirect, url_for, send_from_directory, flash
import os
import subprocess
import xarray as xr

leaf_bp = Blueprint('leaf2', __name__, template_folder='templates')

UPLOAD_FOLDER = 'uploads_leaf'
OUTPUT_FOLDER = 'outputs_leaf'
ALLOWED_EXTENSIONS = {'nc4'}

# Ensure upload and output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@leaf_bp.route('/')
def index():
    return render_template('leaf2.html')

@leaf_bp.route('/process_file', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Get options from the form
        non_leap_year = 'nonLeapYear' in request.form
        add_5_days = 'add5Days' in request.form
        convert_precipitation = 'precipitation' in request.form

        # Open the dataset
        data = xr.open_dataset(file_path)
        out_filename = file_path

        # Apply non-leap year conversion if selected
        if non_leap_year and str(type(data.time.values[0])).__contains__("DatetimeNoLeap"):
            out_filename = file_path.replace(".nc4", "_non_leap_year.nc4")
            try:
                subprocess.run(["bash", "add.leaf.year.sh", file_path, out_filename], check=True)
            except subprocess.CalledProcessError as e:
                flash(f"Script execution failed: {e}")
                return redirect(url_for('index'))

        # Apply add 5 days conversion if selected
        if add_5_days and str(type(data.time.values[0])).__contains__("Datetime360Day"):
            if non_leap_year:
                file_path = out_filename
            out_filename = file_path.replace(".nc4", "_add_5_days.nc4")
            try:
                subprocess.run(["bash", "add.5days.year.sh", file_path, out_filename], check=True)
            except subprocess.CalledProcessError as e:
                flash(f"Script execution failed: {e}")
                return redirect(url_for('index'))

        # Apply precipitation conversion if selected
        if convert_precipitation:
            var = list(data.data_vars)[0]  # assuming 'pr' is the variable name, adjust as necessary
            if var == "pr":
                if add_5_days or non_leap_year:
                    file_path = out_filename
                out_filename = file_path.replace(".nc4", "_mm.nc4")
                try:
                    subprocess.run(["cdo", "mulc,86400", file_path, out_filename], check=True)
                except subprocess.CalledProcessError as e:
                    flash(f"CDO command failed: {e}")
                    return redirect(url_for('index'))

        return send_from_directory(OUTPUT_FOLDER, os.path.basename(out_filename), as_attachment=True)

    flash('Allowed file types are .nc4')
    return redirect(request.url)
