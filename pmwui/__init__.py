import datetime
import shutil
import sys
import threading

import requests
import yaml
import yaml.parser

import os
import subprocess
import uuid

from flask import Flask, request, redirect, jsonify, render_template, abort
from werkzeug.utils import secure_filename

import markdown

from flask_mail import Mail, Message

import logging

import pmwui.db

from pmwui.scheduler import Scheduler

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


def run_pm(uid):
    query_ref = get_query_cmd_data(uid)

    app.logger.info("$$$$$$$$$$$$$$$$$$$$")
    app.logger.info(query_ref)
    app.logger.info("$$$$$$$$$$$$$$$$$$$$")

    filename = f"{uid}.csv"
    ref_data = get_reference_cmd_data(query_ref[0])

    app.logger.info(ref_data)

    ref_path = ref_data[0]
    ref_genome_count = ref_data[1]
    ref_arm_selection = ref_data[2]

    command = f"polymarker.rb -m {os.path.join(app.config['UPLOAD_FOLDER'], filename)} -o {app.static_folder}/data/{uid}_out -c {ref_path} -g {ref_genome_count} -a {ref_arm_selection} -A blast"
    app.logger.info(command)
    result = subprocess.run(command, shell=True)

    app.logger.info(result)

    update_query_status(uid, str(result))

    app.logger.info("_____________")
    app.logger.info(app.static_folder)
    app.logger.info("_____________")

    app.logger.info(os.listdir(app.static_folder))

    os.rename(f"{app.static_folder}/data/{uid}_out/exons_genes_and_contigs.fa",
              f"{app.static_folder}/data/{uid}_out/exons_genes_and_contigs.fa.og")

    post_process_masks(f"{app.static_folder}/data/{uid}_out/exons_genes_and_contigs.fa.og",
                       f"{app.static_folder}/data/{uid}_out/exons_genes_and_contigs.fa")

    rest_done(uid)


scheduler = Scheduler(run_pm)
e = threading.Event()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_references():
    connection = db.connect()
    cursor = connection.cursor()
    cursor.execute("SELECT id, name, description, example FROM reference")
    references = cursor.fetchall()
    connection.close()

    proc_ref = []

    for r in references:
        proc_ref.append(r + (markdown.markdown(r[2]),))

    return proc_ref


def update_query_status(uid, status):
    dbc = db.open_db()
    cursor = dbc.cursor()
    cursor.execute("UPDATE query SET status=? WHERE uid=?", (status, uid))
    dbc.commit()
    cursor.close()
    dbc.close()


def remove_email(uid):
    connection = db.connect()
    cursor = connection.cursor()

    cursor.execute('UPDATE query SET email=NULL WHERE uid=?', (uid,))
    connection.commit()
    connection.close()


def send_massage(to, uid, status, url):
    msg = Message(subject=f'polymarker {uid} {status}', sender='polymarker@nbi.ac.uk',
                  recipients=[to])
    msg.body = f"""The current status of your request ({uid}) is {status}
The latest status and results (when done) are available in: {url}snp_file/{uid}"""
    mail.send(msg)


def index_ref(path):
    app.logger.info(f"path ===== {path}")
    app.logger.info("indexing")
    command = f"samtools faidx {path}"
    result = subprocess.run(command, shell=True)
    if result.returncode > 0:
        app.logger.info(result)
        if result.returncode == 127:
            app.logger.info("samtools not found")
        elif result.returncode == 1:
            app.logger.info(f"failed to open file {path}")
        exit(result.returncode)

    app.logger.info("-------------")

    command = f"makeblastdb -dbtype 'nucl' -in {path} -out {path}"
    result = subprocess.run(command, shell=True)
    if result.returncode > 0:
        app.logger.info("raise hell")
        app.logger.info(result)
        exit(-1)
    app.logger.info("-------------")


def add(path):
    try:
        reference_data_file = open(path)
        try:
            reference_data = yaml.safe_load(reference_data_file)
            app.logger.info("-------")
            try:
                for refs in reference_data:
                    index_ref(refs["path"])
                    db_connection = db.connect()

                    if db_connection is not None:
                        db.create_reference_table(db_connection)
                        db.insert_reference(db_connection, refs)
                        db.create_query_table(db_connection)
            except KeyError:
                app.logger.info("missing path value from reference yaml")
                exit(-1)
        except yaml.parser.ParserError:
            app.logger.info(f"file {path} does not appear to be a valid yaml")
            reference_data_file.close()
            exit(-1)
        reference_data_file.close()
    except FileNotFoundError:
        app.logger.info(f"file {path} not found")
        exit(-1)


@app.post('/snp_files.json')
def snp_files_json():
    data = request.get_json()

    reference = data["snp_file"]["reference"]
    text = data["polymarker_manual_input"]["post"]

    email = data["snp_file"]['email']
    uid = uuid.uuid4()
    reference_id = get_reference_from_name(reference)
    filename = ""

    if text != '':
        filename = f"{uid}.csv"
        file = open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'w')
        file.write(text)
        file.close()

    submit_query(email, filename, reference, reference_id, text, uid)

    return jsonify({"id": uid, "url": f"http://127.0.0.1:5000/snp_file/{uid}", "path": f"/snp_files/{uid}"})


@app.post('/done')
def done():
    data = request.get_json()

    app.logger.info(data)

    uid = data["UID"]
    query_ref = get_query_cmd_data(uid)
    app.logger.info(query_ref)

    if query_ref[1] != "":
        with open(f"{app.static_folder}/data/{uid}_out/status.txt", 'r') as f:
            lines = f.read().splitlines()
            status = lines[-1]
            app.logger.info(status)
            send_massage(query_ref[1], uid, status, "http://127.0.0.1:5000/")

        remove_email(uid)
    return jsonify({"status": "DONE"})


def rest_done(uid):
    url = 'http://127.0.0.1:5000/done'

    data = {
        "UID": uid
    }

    r = requests.post(url, json=data)
    r.raise_for_status()
    app.logger.info(r.json())


def get_reference_from_name(name):
    connection = db.connect()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM reference WHERE name = %s", (name,))
    reference = cursor.fetchone()
    connection.close()
    return reference


def get_reference_cmd_data(ref_id):
    connection = db.connect()
    cursor = connection.cursor()
    cursor.execute("SELECT path, genome_count, arm_selection FROM reference WHERE id = %s", (ref_id,))
    reference = cursor.fetchone()
    connection.close()
    return reference


def get_query_cmd_data(uid):
    connection = db.connect()
    cursor = connection.cursor()
    cursor.execute("SELECT reference, email FROM query WHERE uid = %s", (uid,))
    reference = cursor.fetchone()
    connection.close()
    return reference


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


@app.route("/ver")
def hello_world():
    import importlib.metadata

    version_string_of_foo = importlib.metadata.version('pmwui')
    return f"<p>Hello, World! {version_string_of_foo}</p>"


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
    app.logger.debug('this is a DEBUG message')
    app.logger.info('this is an INFO message')
    app.logger.warning('this is a WARNING message')
    app.logger.error('this is an ERROR message')
    app.logger.critical('this is a CRITICAL message')

    app.logger.info("kjdkjf")

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

        submit_query(email, filename, reference, reference_id, text, uid)
        # return render_template('result.html', id=uid)
        return redirect(f'snp_file/{uid}')

    references = get_references()
    return render_template('index.html', references=references)


def submit_query(email, filename, reference, reference_id, text, uid):
    app.logger.info(f"reference: {reference}")
    app.logger.info(f"reference_id: {reference_id}")
    app.logger.info(f"text: {text}")
    app.logger.info(f"filename: {filename}")
    app.logger.info(f"email: {email}")
    app.logger.info(f"id: {uid}")
    db_connection = db.connect()
    if db_connection is not None:
        db.insert_query(db_connection, uid, reference_id[0], email, datetime.datetime.now())
    scheduler.submit(uid)
    scheduler.poke()
    app.logger.info("########################################")
    if email != "":
        send_massage(email, uid, "New", request.base_url)
    app.logger.info("result: =S")


@app.route('/snp_file/<string:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    app.logger.info(post_id)

    query_ref = get_query_cmd_data(post_id)

    app.logger.info("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    app.logger.info(query_ref)
    app.logger.info("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

    if query_ref is None:
        abort(404)

    status = "init"
    try:
        with open(f"{app.static_folder}/data/{post_id}_out/status.txt", 'r') as f:
            lines = f.read().splitlines()
            status = lines[-1]
    except FileNotFoundError:
        app.logger.info("status file not ready")

    return render_template('res.html', id=post_id, status=status, qcount=scheduler.count())


def remove_old():
    connection = db.connect()
    cursor = connection.cursor()

    one_hour_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)

    select_query = "SELECT id, uid, date FROM query"
    cursor.execute(select_query)
    entries = cursor.fetchall()

    for entry in entries:
        app.logger.info(entry)
        app.logger.info(one_hour_ago)
        app.logger.info(datetime.datetime.fromisoformat(entry[2]))
        if datetime.datetime.fromisoformat(entry[2]) < one_hour_ago:
            cursor.execute("DELETE FROM query WHERE id = ?", (entry[0],))
            app.logger.info("DELETE FROM query WHERE id = ?", (entry[0],))
            try:
                shutil.rmtree(f"{app.static_folder}/data/{entry[1]}_out")
                app.logger.info(f"{app.static_folder}/data/{entry[1]}_out")
            except FileNotFoundError:
                app.logger.info("file not found assume it was never created")
            app.logger.info(f"{cursor.rowcount} rows were deleted.")
            connection.commit()

    cursor.close()
    connection.close()


@app.post('/gc')
def gc():
    remove_old()
    return jsonify({"status": "DONE"})


def gc_post():
    url = 'http://127.0.0.1:5000/gc'
    pm_test_data = {

    }
    r = requests.post(url, json=pm_test_data)
    r.raise_for_status()
    app.logger.info(r.json())


def main():
    app.logger.debug('this is a DEBUG message')
    app.logger.info('this is an INFO message')
    app.logger.warning('this is a WARNING message')
    app.logger.error('this is an ERROR message')
    app.logger.critical('this is a CRITICAL message')

    if len(sys.argv) > 1:
        if sys.argv[1] == "add":
            if len(sys.argv) >= 3:
                for conf in sys.argv[2:]:
                    add(conf)
            else:
                app.logger.info("invalid options")
            exit(0)
        elif sys.argv[1] == "init":
            db.init_db()
            exit(0)
        elif sys.argv[1] == "gc":
            gc_post()
            exit(0)

    scheduler.start()
    app.run(debug=True)
    scheduler.stop()


def server():
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    scheduler.start()
    return app
