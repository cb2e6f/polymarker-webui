import datetime
import shutil
import sys
import threading
from asyncio import sleep

import requests
import yaml
import yaml.parser

import os
import subprocess
import uuid

from flask import Flask, flash, request, redirect, jsonify, render_template, url_for, abort
from werkzeug.utils import secure_filename

from .db import *

import markdown

from flask_mail import Mail, Message

# from post_process_masks import post_process_masks


# UPLOAD_FOLDER = '/usr/users/JIC_a5/goz24vof/uploads'
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config['MAIL_SERVER'] = 'webmail.nbi.ac.uk'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'polymarker'
app.config['MAIL_PASSWORD'] = 'Parrot14'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
# app.config['MAIL_DEBUG'] = True

mail = Mail(app)

e = threading.Event()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_references():
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, description, example FROM reference")
    references = cursor.fetchall()
    connection.close()

    proc_ref = []

    for r in references:
        proc_ref.append(r + (markdown.markdown(r[2]),))

    return proc_ref


# # Define a route for the home page
# @app.route('/')
# def hello_world():
#     return 'Hello, World!!!E!!!!'


# Define another route for a different page
@app.route('/greet')
def greet():
    return f'Hello, {request.url_root}!'


def send_massage(to, uid, status, url):
    msg = Message(subject=f'polymarker {uid} {status}', sender='polymarker@nbi.ac.uk',
                  recipients=[to])
    msg.body = f"""The current status of your request ({uid}) is {status}
The latest status and results (when done) are available in: {url}snp_file/{uid}"""
    mail.send(msg)


@app.route("/mtest")
def mtest():
    send_massage("rob.ellis@jic.ac.uk", 111111, "GOOD")
    return "Message sent!"


def index_ref(path):
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


def create_query_table(connection):
    cursor = connection.cursor()

    query = """
    CREATE TABLE IF NOT EXISTS query (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        uid TEXT,
        reference TEXT,
        email TEXT,
        date TEXT,
        status TEXT        
    );
    """

    try:
        cursor.execute(query)
        connection.commit()
        print(f"created query table: {query}")
    except mariadb.Error as e:
        print(f"error creating query table: {e}")


def insert_reference(connection, config):
    cursor = connection.cursor()

    query = """
    INSERT INTO reference (name, path, genome_count, arm_selection, description, example)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(config["example"])
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    try:
        cursor.execute(query, (
            config["name"], config["path"], config["genome_count"], config["arm_selection"], config["description"],
            config["example"]))
        connection.commit()
        print(f"inserted reference: {query}")
    except mariadb.Error as e:
        print(f"error inserting reference: {e}")


def insert_query(connection, uid, reference, email, date):
    cursor = connection.cursor()

    query = """
    INSERT INTO query (uid, reference, email, date)
    VALUES (?, ?, ?, ?)
    """

    try:
        cursor.execute(query, (uid, reference, email, date))
        connection.commit()
        print(f"inserted query: {query}")
    except mariadb.Error as e:
        print(f"error inserting query: {e}")



def add(path):
    try:
        reference_data_file = open(path)
        try:
            reference_data = yaml.safe_load(reference_data_file)
            print("-------")
            try:
                for refs in reference_data:
                    index_ref(refs["path"])
                    db_connection = connect()

                    if db_connection is not None:
                        create_reference_table(db_connection)
                        insert_reference(db_connection, refs)
                        create_query_table(db_connection)
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


@app.post('/echo')
def echo():
    data = request.get_json()
    return jsonify(data)

@app.post('/snp_files.json')
def snp_files_json():
    data = request.get_json()


    reference = data["snp_file"]["reference"]
    text = data["polymarker_manual_input"]["post"]

    email = data["snp_file"]['email']
    uid = uuid.uuid4()
    reference_id = get_reference_from_name(reference)

    if text != '':
        filename = f"{uid}.csv"
        file = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'w')
        file.write(text)
        file.close()

    print(f"reference: {reference}")
    print(f"reference_id: {reference_id}")
    print(f"text: {text}")
    print(f"filename: {filename}")
    print(f"email: {email}")
    print(f"id: {uid}")

    db_connection = connect()

    if db_connection is not None:
        insert_query(db_connection, uid, reference_id[0], email, datetime.datetime.now())

    submit(uid)

    e.set()
    e.clear()

    print("########################################")

    if email != "":
        pass
        # send_massage(email, uid, "New", request.base_url)

    print(f"result: =S")

    return jsonify({"id": uid, "url": f"http://127.0.0.1:5000/snp_file/{uid}", "path": f"/snp_files/{uid}"})



@app.post('/done')
def done():
    data = request.get_json()

    print(data)

    uid = data["UID"]
    ref = get_query_cmd_data(uid)
    print(ref)

    if ref[1] != "":
        with open(f"{app.static_folder}/data/{uid}_out/status.txt", 'r') as f:
            lines = f.read().splitlines()
            status = lines[-1]
            print(status)
            # send_massage(ref[1], uid, status,"http://127.0.0.1:5000/")

    return jsonify({"status": "DONE"})

def rest_done(uid):
    url = 'http://127.0.0.1:5000/done'

    data = {
        "UID": uid
    }

    r = requests.post(url, json=data)
    r.raise_for_status()
    print(r.json())

def get_reference_from_name(name):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM reference WHERE name = %s", (name,))
    reference = cursor.fetchone()
    connection.close()
    return reference


def get_reference_cmd_data(ref_id):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT path, genome_count, arm_selection FROM reference WHERE id = %s", (ref_id,))
    reference = cursor.fetchone()
    connection.close()
    return reference


def get_query_cmd_data(uid):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute("SELECT reference, email FROM query WHERE uid = %s", (uid,))
    reference = cursor.fetchone()
    connection.close()
    return reference


@app.route('/ref', methods=['GET', 'POST'])
def ref():
    message = ''

    if request.method == 'POST':
        # selected_name = request.form['reference']

        print(request.form)

        # print(selected_name)

        # file_name = request.form['file_name']
        #
        # connection = db.connect()
        # cursor = connection.cursor()
        # cursor.execute("SELECT id FROM reference WHERE name = ?", (selected_name,))
        # reference_id = cursor.fetchone()[0]
        # connection.close()
        #
        # # Process the file with the selected employee ID
        message = "some message"  # process_file(file_name, employee_id)

    # Get the list of employees for the dropdown
    references = get_references()

    return render_template('ref.html', references=references, message=message)


@app.route('/about', methods=['GET'])
def about():
    references = get_references()
    return render_template('about.html', references=references)


@app.route('/cite', methods=['GET'])
def cite():
    return render_template('cite.html')


@app.route('/designed_primers', methods=['GET'])
def designed():
    return render_template('designed.html')


@app.route('/idx', methods=['GET'])
def idx():
    return render_template('index2.html')


@app.route('/res', methods=['GET'])
def res():
    return render_template('res.html')


def post_process_masks(src, des):
    src_file = open(src, 'r')
    des_file = open(des, 'w')

    mask = False
    skip = False

    for line in src_file:
        if skip and line.startswith(">"):
            skip = False

        if mask and line.startswith(">"):
            skip = True
            mask = False
            continue

        if line.startswith(">MASK"):
            mask = True

        if skip:
            continue

        des_file.write(line)

    des_file.close()
    src_file.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # print(request.form)
        reference = request.form['reference']


        if "text" in request.form:
            text = request.form['text']
        else:
            text = ''



        filename = ''
        if 'file' in request.files:
            file = request.files['query_file']

            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        email = request.form['email']
        uid = uuid.uuid4()
        reference_id = get_reference_from_name(reference)

        if filename == '' and text != '':
            filename = f"{uid}.csv"
            file = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'w')
            file.write(text)
            file.close()

        print(f"reference: {reference}")
        print(f"reference_id: {reference_id}")
        print(f"text: {text}")
        print(f"filename: {filename}")
        print(f"email: {email}")
        print(f"id: {uid}")

        db_connection = connect()

        if db_connection is not None:
            insert_query(db_connection, uid, reference_id[0], email, datetime.datetime.now())

        submit(uid)

        e.set()
        e.clear()

        print("########################################")

        if email != "":
            pass
            # send_massage(email, uid, "New", request.base_url)

        print(f"result: =S")
        # return render_template('result.html', id=uid)
        return redirect(f'snp_file/{uid}')

    references = get_references()
    return render_template('index.html', references=references)


def run_pm(uid):
    ref = get_query_cmd_data(uid)

    print("$$$$$$$$$$$$$$$$$$$$")
    print(ref)
    print("$$$$$$$$$$$$$$$$$$$$")

    filename = f"{uid}.csv"
    ref_data = get_reference_cmd_data(ref[0])

    print(ref_data)

    ref_path = ref_data[0]
    ref_genome_count = ref_data[1]
    ref_arm_selection = ref_data[2]

    command = f"polymarker.rb -m {os.path.join(app.config['UPLOAD_FOLDER'], filename)} -o {app.static_folder}/data/{uid}_out -c {ref_path} -g {ref_genome_count} -a {ref_arm_selection} -A blast"
    print(command)
    result = subprocess.run(command, shell=True)

    print(result)

    db.update_query_status(uid, str(result))

    print("_____________")
    print(app.static_folder)
    print("_____________")

    print(os.listdir(app.static_folder))

    os.rename(f"{app.static_folder}/data/{uid}_out/exons_genes_and_contigs.fa",
              f"{app.static_folder}/data/{uid}_out/exons_genes_and_contigs.fa.og")

    post_process_masks(f"{app.static_folder}/data/{uid}_out/exons_genes_and_contigs.fa.og",
                       f"{app.static_folder}/data/{uid}_out/exons_genes_and_contigs.fa")

    rest_done(uid)

@app.route('/snp_file/<string:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    print(post_id)

    ref = get_query_cmd_data(post_id)

    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    print(ref)
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")



    if ref is None:
        abort(404)


    status = "init"
    try:
        with open(f"{app.static_folder}/data/{post_id}_out/status.txt", 'r') as f:
            lines = f.read().splitlines()
            status = lines[-1]
    except FileNotFoundError:
        print("status file not ready")

    return render_template('res.html', id=post_id, status=status, qcount=db.count())


def remove_old():
    connection = connect()
    cursor = connection.cursor()

    one_hour_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)

    select_query = "SELECT id, uid, date FROM query"
    cursor.execute(select_query)
    entries = cursor.fetchall()


    for e in entries:
        print(e)
        print(one_hour_ago)
        print(datetime.datetime.fromisoformat(e[2]))
        if datetime.datetime.fromisoformat(e[2]) < one_hour_ago:
            cursor.execute("DELETE FROM query WHERE id = ?", (e[0],))
            print("DELETE FROM query WHERE id = ?", (e[0],))
            shutil.rmtree(f"{app.static_folder}/data/{e[1]}_out")
            print(f"{app.static_folder}/data/{e[1]}_out")
            print(f"{cursor.rowcount} rows were deleted.")
            connection.commit()

    cursor.close()
    connection.close()

def worker(cv, s):
    while True:
        work = db.get(s)
        if work is not None:
            sleep(3)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            print(work)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            try:
                run_pm(work[1])
            except Exception as e:
                print(e)
                db.update_query_status(work[1], "E: " + str(e))
            # db.update(work[0], "DONE")
            db.delete(work[0])
        else:
            print("...")
            cv.wait()


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "add":
            if len(sys.argv) >= 3:
                for conf in sys.argv[2:]:
                    add(conf)
            else:
                print("invalid options")
            exit(0)
        elif sys.argv[1] == "init":
            init_db()
            exit(0)

    # remove_old()
    # exit()


    print("££££££££££££££££")
    print(db.count())
    print("££££££££££££££££")

    print("#######################")
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('UPDATE cmd_queue SET status = "SUB" WHERE status = "GOT"')
    connection.commit()
    connection.close()
    print("#######################")

    # e = threading.Event()
    s = threading.Semaphore()

    worker1 = threading.Thread(target=worker, args=(e, s))
    worker1.start()

    worker2 = threading.Thread(target=worker, args=(e, s))
    worker2.start()

    e.set()
    e.clear()

    app.run(debug=True)

    worker1.join()
    worker2.join()


if __name__ == "__main__":
    main()
