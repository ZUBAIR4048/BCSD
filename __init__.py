from flask import Flask, render_template
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = 'supersecretkey'

    # Configure upload and output folders
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

    # Ensure upload and output directories exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['OUTPUT_FOLDER']):
        os.makedirs(app.config['OUTPUT_FOLDER'])

    # Register your existing blueprints
    from .merge_step import merge_bp
    from .curvilinear import curvilinear_bp
    from .leaf2 import leaf_bp
    from .partition import partition_bp
    from app import bias_correction
    #from .bias_org import bias_bp
    #from .stats import stats_bp
    from .regriding_step import regriding_bp
    from .variable_selection import variable_selection_bp
    from .bias_correction import bias_correction_bp
    from app import statistical_downscaling
    from app.statistical_downscaling import statistical_downscaling_bp
    from .projection import projection_bp
    from .about import about_bp
    app.register_blueprint(merge_bp, url_prefix='/merge')
    app.register_blueprint(curvilinear_bp, url_prefix='/crvlinear2')
    app.register_blueprint(leaf_bp, url_prefix='/leaf2')
    app.register_blueprint(partition_bp, url_prefix='/partition')
    #app.register_blueprint(bias_bp, url_prefix='/bias_now')
    #app.register_blueprint(stats_bp, url_prefix='/stats')
    app.register_blueprint(regriding_bp, url_prefix='/regriding')
    app.register_blueprint(variable_selection_bp, url_prefix='/variable_selection')
    #app.register_blueprint(bias_correction_bp)
    app.register_blueprint(about_bp, url_prefix='/about')
    # Import and register the new bias correction module
    #from app.bias_correction import bias_correction_bp
    app.register_blueprint(bias_correction_bp, url_prefix='/bias_now')
    app.register_blueprint(statistical_downscaling_bp, url_prefix='/stats2')
    app.register_blueprint(projection_bp, url_prefix='/projection')

    @app.route('/')
    def index():
        return render_template('main.html')

    return app
