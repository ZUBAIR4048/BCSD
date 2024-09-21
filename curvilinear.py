from flask import Blueprint, request, render_template, redirect, url_for, flash, send_file
import os
import subprocess

curvilinear_bp = Blueprint('curvilinear', __name__, template_folder='app/templates')

UPLOAD_FOLDER = 'uploads_curvilinear'
OUTPUT_FOLDER = 'outputs_curvilinear'
ALLOWED_EXTENSIONS = {'nc4', 'nc'}  # Corrected this line to properly set allowed extensions

# Ensure upload and output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@curvilinear_bp.route('/')
def index():
    return render_template('crvlinear2.html')

@curvilinear_bp.route('/upload', methods=['POST'])
def upload_file():
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

        # Get grid parameters from the form
        try:
            firstLat = float(request.form['firstLat'])
            firstLon = float(request.form['firstLon'])
            degreeInc = float(request.form['degreeInc'])
            lastLat = float(request.form['lastLat'])
            lastLon = float(request.form['lastLon'])
        except ValueError:
            flash('Invalid grid parameter values')
            return redirect(request.url)

        # Calculate grid sizes and other parameters
        xsize = int((lastLon - firstLon) / degreeInc)
        ysize = int((lastLat - firstLat) / degreeInc)
        gridsize = xsize * ysize
        xfirst = firstLon
        yfirst = firstLat
        xinc = degreeInc
        yinc = degreeInc

        # Create the grid definition string
        grid_definition = f"""
gridtype  = lonlat
gridsize  = {gridsize}
datatype  = float
xsize     = {xsize}
ysize     = {ysize}
xname     = lon
xlongname = "longitude"
xunits    = "degrees_east"
yname     = lat
ylongname = "latitude"
yunits    = "degrees_north"
xfirst    = {xfirst}
xinc      = {xinc}
yfirst    = {yfirst}
yinc      = {yinc}
scanningMode = 64
        """.strip()
        
        temp_grid_path = os.path.join(UPLOAD_FOLDER, 'regular_grid_pak.txt')
        with open(temp_grid_path, "w") as temp_grid_file:
            temp_grid_file.write(grid_definition)

        outfile_name_regrid = filename.replace(".nc4", "_regrid.nc4")
        outfile_name_regrid_path = os.path.join(OUTPUT_FOLDER, outfile_name_regrid)
        
        try:
            subprocess.run(["cdo", f"remapbil,{temp_grid_path}", file_path, outfile_name_regrid_path], check=True)
            # Keep the template open and render the template with a success message
            return render_template('crvlinear2.html', download_url=url_for('curvilinear.download_file', filename=outfile_name_regrid))
        
        except subprocess.CalledProcessError as e:
            flash(f"CDO command failed: {e}")
            return redirect(url_for('curvilinear.index'))
    
    flash('Allowed file types are .nc4')
    return redirect(url_for('curvilinear.index'))

@curvilinear_bp.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """ Route to download the file. """
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

