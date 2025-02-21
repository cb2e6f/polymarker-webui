import subprocess
import sys

import mariadb
import yaml
from flask import Flask

# Create the Flask application
app = Flask(__name__)


# Define a route for the home page
@app.route('/')
def hello_world():
    return 'Hello, World!!!E!!!!'


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
