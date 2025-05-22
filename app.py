from flask import Flask, render_template, request, redirect, url_for, session, flash,send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
from FixedSpeed import ten_coefficients

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsm', 'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_type = request.form.get('compressor_type')
        if selected_type == "Fixed Speed":
            return redirect(url_for('fixed_speed'))
        elif selected_type == "Variable Speed":
            return redirect(url_for('variable_speed'))
    return render_template('index.html')


@app.route("/fixed", methods=["GET", "POST"])
def fixed_speed():
    file_uploaded = False
    filename = None

    if request.method == "POST":
        if 'data_file' in request.files:
            file = request.files['data_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                session['uploaded_file'] = filepath
                               # Save selected units in session
                session['temp_unit'] = request.form.get('temp_unit')
                session['capacity_unit'] = request.form.get('capacity_unit')
                session['power_unit'] = request.form.get('power_unit')
                session['massflow_unit'] = request.form.get('massflow_unit')

                session['filename'] = filename
                file_uploaded = True
                flash(f"Successfully uploaded: {filename}", "success")
            else:
                flash("Invalid file type. Only .xlsm and .csv allowed.", "danger")

        elif 'continue_flag' in request.form:
            return redirect(url_for("show_results"))

    return render_template("fixed.html", file_uploaded=file_uploaded, filename=session.get('filename'),)


@app.route("/show_results")
def show_results():
    filepath = session.get('uploaded_file')
    if not filepath:
        return "No file found in session. Please upload again."
    
    # Get units from session
    units = {
        "temperature": session.get("temp_unit"),
        "capacity": session.get("capacity_unit"),
        "power": session.get("power_unit"),
        "massflow": session.get("massflow_unit")
    }

    try:
        coefficients, output_path = ten_coefficients(upload_folder=app.config['UPLOAD_FOLDER'],units = units)
        session['output_excel'] = output_path  # store the path for download
        return render_template("result.html", coefficients=coefficients)


    except Exception as e:
        return f"<h2>Error reading uploaded file:</h2><pre>{str(e)}</pre>"

@app.route("/download_excel")
def download_excel():
    output_path = session.get('output_excel')
    if not output_path or not os.path.exists(output_path):
        return "No output file found. Please generate coefficients first."
    return send_file(output_path, as_attachment=True)

@app.route('/variable', methods=['GET', 'POST'])
def variable_speed():
    result = None
    if request.method == 'POST':
        suction = request.form.get('suction_temp')
        discharge = request.form.get('discharge_temp')
        frequency = request.form.get('frequency')
        result = f"Variable Speed Coefficients calculated for Suction: {suction}, Discharge: {discharge}, Freq: {frequency}"
    return render_template('variable.html', result=result)


if __name__ == '__main__':
    app.run(debug=True)
