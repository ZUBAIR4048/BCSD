from flask import render_template, request, redirect, url_for

@app.route('/bias_now', methods=['POST'])
def bias_selection():
    variable = request.args.get('variable')
    return redirect(url_for(f'bias_now.bias_{variable}'))
@app.route('/stats2', methods=['POST'])
def bias_selection():
    variable = request.args.get('variable')
    return redirect(url_for(f'stats2.bias_{variable}'))
