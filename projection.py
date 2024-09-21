import os
import tempfile
import xarray as xr
import seaborn as sns
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename

projection_bp = Blueprint('projection', __name__)

@projection_bp.route('/')
def projection():
    return render_template('projection.html')

@projection_bp.route('/upload', methods=['POST'])
def upload_files():
    if 'file1' not in request.files or 'file2' not in request.files:
        flash("Please upload both required files.", "error")
        return redirect(url_for('projection.projection'))

    file1 = request.files['file1']
    file2 = request.files['file2']

    try:
        # Save the uploaded files to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath1 = os.path.join(temp_dir, secure_filename(file1.filename))
            filepath2 = os.path.join(temp_dir, secure_filename(file2.filename))
            file1.save(filepath1)
            file2.save(filepath2)

            # Load the NetCDF files
            ob_data_part1 = xr.open_dataset(filepath1)
            model_data_part1 = xr.open_dataset(filepath2)

            # Process data and create the plot
            ob_df = ob_data_part1['hurs'].mean(dim=['lat', 'lon']).to_dataframe()
            model_df = model_data_part1['hurs'].mean(dim=['lat', 'lon']).to_dataframe()

            # Plot with labels
            sns.kdeplot(ob_df['hurs'], color='blue', label=f'Observed: {file1.filename}')
            sns.kdeplot(model_df['hurs'], color='red', label=f'Model: {file2.filename}')
            plt.title("Projection Analysis")
            plt.xlabel('Hurs Values')
            plt.ylabel('Density')
            plt.legend()

            # Save the plot to a file
            plot_path = os.path.join(temp_dir, "projection_plot.png")
            plt.savefig(plot_path)

            # Serve the plot to the user
            return send_file(plot_path, mimetype='image/png')

    except Exception as e:
        flash(f"An error occurred while processing the files: {str(e)}", "error")
        return redirect(url_for('projection.projection'))
