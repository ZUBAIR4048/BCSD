from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, current_app
import os
import subprocess
from werkzeug.utils import secure_filename
import xarray as xr
import tempfile

regriding_bp = Blueprint('regriding', __name__, template_folder='templates')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'nc', 'nc4'}

@regriding_bp.route('/')
def index():
    return render_template('regriding.html')

@regriding_bp.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('regriding.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('regriding.index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path = os.path.join(temp_dir, filename)
            file.save(upload_path)

            # Generate output filenames for ncpdq and cdo commands
            ncpdq_output_filename = f"{os.path.splitext(filename)[0]}_ncpdq.nc"
            ncpdq_output_path = os.path.join(temp_dir, ncpdq_output_filename)

            cdo_output_filename = f"{os.path.splitext(filename)[0]}_regrid.nc"
            cdo_output_path = os.path.join(temp_dir, cdo_output_filename)

            try:
                # Run the ncpdq command
                subprocess.run(['ncpdq', '--rdr=time,lat,lon', upload_path, ncpdq_output_path], check=True)

                # Get grid parameters from the form
                try:
                    firstLat = float(request.form['firstLat'])
                    firstLon = float(request.form['firstLon'])
                    degreeInc = float(request.form['degreeInc'])
                    lastLat = float(request.form['lastLat'])
                    lastLon = float(request.form['lastLon'])
                except ValueError:
                    flash('Invalid grid parameter values')
                    return redirect(url_for('regriding.index'))

                # Calculate grid sizes and other parameters
                xsize = int((lastLon - firstLon) / degreeInc) + 1
                ysize = int((lastLat - firstLat) / degreeInc) + 1
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

                griddes_path = os.path.join(temp_dir, 'griddes.txt')
                with open(griddes_path, "w") as griddes_file:
                    griddes_file.write(grid_definition)

                # Run the cdo command
                subprocess.run(['cdo', f'remapbil,{griddes_path}', ncpdq_output_path, cdo_output_path], check=True)

                # Modify lat and lon values
                ds = xr.open_dataset(cdo_output_path)
                lat_values = ds['lat'].values
                lon_values = ds['lon'].values

                lat_values[0] -= 0.025
                lat_values[-1] += 0.025
                lon_values[0] -= 0.025
                lon_values[-1] += 0.025

                ds = ds.assign_coords(lat=lat_values, lon=lon_values)

                # Save the final file to a temporary path
                final_output_path = os.path.join(temp_dir, f"{os.path.splitext(filename)[0]}_final.nc")
                ds.to_netcdf(final_output_path)

                # Send the file for download
                return send_file(final_output_path, as_attachment=True, download_name=f"{os.path.splitext(filename)[0]}_final.nc")

            except subprocess.CalledProcessError as e:
                flash(f"Command failed: {e}")
                return redirect(url_for('regriding.index'))

    flash('File processing failed.')
    return redirect(url_for('regriding.index'))
