import os
import subprocess
import uuid

import mariadb
from flask import Flask, flash, request, redirect, jsonify, render_template
from werkzeug.utils import secure_filename

from post_process_masks import post_process_masks

UPLOAD_FOLDER = '/usr/users/JIC_a5/goz24vof/uploads'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.post('/echo')
def echo():
    data = request.get_json()
    return jsonify(data)


def get_references():
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name FROM reference")
    references = cursor.fetchall()
    connection.close()
    return references


def get_reference_from_name(name):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM reference WHERE name = %s", (name,))
    reference = cursor.fetchone()
    connection.close()
    return reference

def get_referece_cmd_data(id):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT path, genome_count, arm_selection FROM reference WHERE id = %s", (id,))
    reference = cursor.fetchone()
    connection.close()
    return reference


def connect():
    try:
        connection = mariadb.connect(
            user="re",
            password="",
            host="localhost",
            port=3306,
            database="cmd_queue_db"
        )
        return connection
    except mariadb.Error as e:
        print(f"error connecting to mariadb: {e}")
        return None


@app.route('/ref', methods=['GET', 'POST'])
def ref():
    message = ''

    if request.method == 'POST':
        selected_name = request.form['reference']

        print(request.form)

        # print(selected_name)

        # file_name = request.form['file_name']
        #
        # connection = db.connect()
        # cursor = connection.cursor()
        # cursor.execute("SELECT id FROM reference WHERE name = ?", (selected_name,))
        # refernce_id = cursor.fetchone()[0]
        # connection.close()
        #
        # # Process the file with the selected employee ID
        message = "blegh"  # process_file(file_name, employee_id)

    # Get the list of employees for the dropdown
    references = get_references()

    return render_template('ref.html', references=references, message=message)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        reference = request.form['reference']
        text = request.form['text']

        filename = ''
        if 'file' in request.files:
            file = request.files['file']

            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        email = request.form['email']
        id = uuid.uuid4()
        reference_id = get_reference_from_name(reference)

        print(f"reference: {reference}")
        print(f"reference_id: {reference_id}")
        print(f"text: {text}")
        print(f"filename: {filename}")
        print(f"email: {email}")
        print(f"id: {id}")

        if filename == '' and text != '':
            filename = f"{id.hex}.csv"
            file = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'w')
            file.write(text)
            file.close()

        ref_data = get_referece_cmd_data(reference_id[0])

        print(ref_data)

        ref_path = ref_data[0]
        ref_genome_count = ref_data[1]
        ref_arm_selection = ref_data[2]

        command = f"polymarker.rb -m {os.path.join(app.config['UPLOAD_FOLDER'], filename)} -o static/data/{id}_out -c {ref_path} -g {ref_genome_count} -a {ref_arm_selection} -A blast"
        print(command)
        result = subprocess.run(command, shell=True)

        os.rename(f"static/data/{id}_out/exons_genes_and_contigs.fa", f"static/data/{id}_out/exons_genes_and_contigs.fa.og")

        post_process_masks(f"static/data/{id}_out/exons_genes_and_contigs.fa.og", f"static/data/{id}_out/exons_genes_and_contigs.fa")

        print(f"result: {result}")
        return render_template('results.html', id=id)


    references = get_references()
    return render_template('index.html', references=references)


@app.route('/2', methods=['GET', 'POST'])
def index2():
    if request.method == 'POST':
        flash("Youve been posted")
        print(request.files)
        print(request.form)

        print(request.files['file'].filename)

        reference = request.form['reference']
        text = request.form['text']
        email = request.form['email']

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part, how did we get here?')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(request.url)

    references = get_references()
    return render_template('index.html', references=references)