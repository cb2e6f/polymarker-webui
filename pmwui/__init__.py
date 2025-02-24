import subprocess
import sys

import mariadb
import yaml
from flask import Flask, jsonify, request


import os
import subprocess
import uuid

import mariadb
from flask import Flask, flash, request, redirect, jsonify, render_template
from werkzeug.utils import secure_filename

# from post_process_masks import post_process_masks



# UPLOAD_FOLDER = '/usr/users/JIC_a5/goz24vof/uploads'
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def get_references():
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name FROM reference")
    references = cursor.fetchall()
    connection.close()
    return references

# # Define a route for the home page
# @app.route('/')
# def hello_world():
#     return 'Hello, World!!!E!!!!'


# Define another route for a different page
@app.route('/greet/<name>')
def greet(name):
    return f'Hello, {name}!'

def index(path):
    print(f"path ===== {path}")
    print("indexing")
    command = f"samtools faidx {path}"
    result = subprocess.run(command, shell=True)
    if result.returncode > 0:
        print(result)
        if result.returncode == 127:
            print("samtools not found")
        elif result.returncode == 1:
            print(f"failed to open file {path}")
        exit(result.returncode)

    print("-------------")

    command = f"makeblastdb -dbtype 'nucl' -in {path} -out {path}"
    result = subprocess.run(command, shell=True)
    if result.returncode > 0:
        print("raise hell")
        print(result)
        exit(-1)
    print("-------------")


def connect():
    try:
        connection = mariadb.connect(
            user="re",
            password="",
            host="localhost",
            port=3306,
            database="polymarker_webui"
        )
        return connection
    except mariadb.Error as e:
        print(f"error connecting to mariadb: {e}")
        return None


def create_reference_table(connection):
    cursor = connection.cursor()

    query = """
    CREATE TABLE IF NOT EXISTS reference (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        name TEXT,
        path TEXT,
        genome_count TEXT,
        arm_selection TEXT,
        description TEXT,
        example TEXT        
    );
    """

    try:
        cursor.execute(query)
        connection.commit()
        print(f"created reference table: {query}")
    except mariadb.Error as e:
        print(f"error creating reference table: {e}")


def insert_reference(connection, config):
    cursor = connection.cursor()

    query = """
    INSERT INTO reference (name, path, genome_count, arm_selection, description, example)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    try:
        cursor.execute(query, (
            config["name"], config["path"], config["genome_count"], config["arm_selection"], config["description"],
            config["example"]))
        connection.commit()
        print(f"inserted reference: {query}")
    except mariadb.Error as e:
        print(f"error inserting reference: {e}")




def add(path):

    try:
        reference_data_file = open(path)
        try:
            reference_data = yaml.safe_load(reference_data_file)
            print("-------")
            try:
                for ref in reference_data:
                    index(ref["path"])
                    db_connection = connect()

                    if db_connection is not None:
                        create_reference_table(db_connection)
                        insert_reference(db_connection, ref)
            except KeyError:
                print(f"missing path value from reference yaml")
                exit(-1)
        except yaml.parser.ParserError:
            print(f"file {path} does not appear to be a valid yaml")
            reference_data_file.close()
            exit(-1)
        reference_data_file.close()
    except FileNotFoundError:
        print(f"file {path} not found")
        exit(-1)




########################################################################





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
            database="polymarker_webui"
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

        print(os.listdir("."))

        # os.rename(f"static/data/{id}_out/exons_genes_and_contigs.fa",
        #           f"static/data/{id}_out/exons_genes_and_contigs.fa.og")

        # post_process_masks(f"static/data/{id}_out/exons_genes_and_contigs.fa.og", f"static/data/{id}_out/exons_genes_and_contigs.fa")

        print(f"result: {result}")
        return render_template('result.html', id=id)


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


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "add":
            if len(sys.argv) >= 3:
                for conf in sys.argv[2:]:
                    add(conf)
            else:
                print("invalid options")
            exit(0)
    app.run(debug=True)


if __name__ == "__main__":
    main()
