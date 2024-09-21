from flask import Blueprint, request, render_template, redirect, url_for, send_file, flash
import subprocess
import os

partition_bp = Blueprint('partition', __name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'nc4'}

# Ensure upload and output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@partition_bp.route('/')
def index():
    return render_template('partition2.html')

@partition_bp.route('/process_dates', methods=['POST'])
def process_dates():
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

        # Get dates from the form
        start_date = request.form['startDate']
        hist_enddate = request.form['historicalEndDate']
        fut_enddate = request.form['futureEndDate']

        # Generate output filenames
        base_name = os.path.splitext(filename)[0]
        
        # Historical file names
        out_filename_hist = os.path.join(OUTPUT_FOLDER, f"{base_name}_sim_hist_{start_date}_{hist_enddate}.nc4")
        out_filename_hist_re = os.path.join(OUTPUT_FOLDER, f"{base_name}_sim_hist_{start_date}_{hist_enddate}_re.nc4")
        out_filename_hist_fi = os.path.join(OUTPUT_FOLDER, f"{base_name}_sim_hist_{start_date}_{hist_enddate}_fi.nc4")
        
        # Future file names
        out_filename_fut = os.path.join(OUTPUT_FOLDER, f"{base_name}_sim_fut_{start_date}_{fut_enddate}.nc4")
        out_filename_fut_re = os.path.join(OUTPUT_FOLDER, f"{base_name}_sim_fut_{start_date}_{fut_enddate}_re.nc4")
        out_filename_fut_fi = os.path.join(OUTPUT_FOLDER, f"{base_name}_sim_fut_{start_date}_{fut_enddate}_fi.nc4")
        
        # Process historical data
        subprocess.run(["cdo", f"seldate,{start_date},{hist_enddate}", file_path, out_filename_hist], check=True)
        subprocess.run(["ncpdq", "--rdr=lon,lat,time", out_filename_hist, out_filename_hist_re], check=True)
        subprocess.run(["ncks", "--fix_rec_dmn", "lon", out_filename_hist_re, out_filename_hist_fi], check=True)
        
        # Process future data
        subprocess.run(["cdo", f"seldate,{start_date},{fut_enddate}", file_path, out_filename_fut], check=True)
        subprocess.run(["ncpdq", "--rdr=lon,lat,time", out_filename_fut, out_filename_fut_re], check=True)
        subprocess.run(["ncks", "--fix_rec_dmn", "lon", out_filename_fut_re, out_filename_fut_fi], check=True)

        # Present download buttons for both files after processing
        return render_template('partition2.html', 
                               hist_file=os.path.basename(out_filename_hist_fi), 
                               fut_file=os.path.basename(out_filename_fut_fi))

    flash('Allowed file types are .nc4')
    return redirect(url_for('partition.index'))

@partition_bp.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(file_path, as_attachment=True, download_name=filename, mimetype='application/x-netcdf')
