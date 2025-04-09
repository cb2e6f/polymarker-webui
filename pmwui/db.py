import logging

import mariadb

logger = logging.getLogger('gunicorn.error')


def open_db():
    dbc = mariadb.connect(
        host="localhost",
        user="polymarker",
        password="",
        database="polymarker_webui"
    )

    logger.info("on open")

    return dbc


def connect():
    logger.info("on connect")
    try:
        connection = mariadb.connect(
            user="polymarker",
            password="",
            host="localhost",
            port=3306,
            database="polymarker_webui"
        )
        return connection
    except mariadb.Error as exception:
        # app.logger.info(f"error connecting to mariadb: {exception}")
        print(f"error connecting to mariadb: {exception}")
        return None


def init_db():
    dbc = mariadb.connect(
        host="localhost",
        user="polymarker",
        password="",
    )

    cursor = dbc.cursor()
    # cursor.execute("DROP DATABASE IF EXISTS polymarker_webui")
    # cursor.execute("CREATE DATABASE polymarker_webui")
    cursor.execute("USE polymarker_webui")
    cursor.execute(
        "CREATE TABLE cmd_queue(id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL, cmd TEXT NOT NULL, status TEXT NOT NULL)")
    dbc.commit()

    cursor.close()
    dbc.close()

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
        # app.logger.info(f"created reference table: {query}")
        print(f"created reference table: {query}")
    except mariadb.Error as exception:
        # app.logger.info(f"error creating reference table: {exception}")
        print(f"error creating reference table: {exception}")


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
        # app.logger.info(f"created query table: {query}")
        print(f"created query table: {query}")
    except mariadb.Error as exception:
        # app.logger.info(f"error creating query table: {exception}")
        print(f"error creating query table: {exception}")


def insert_reference(connection, config):
    cursor = connection.cursor()

    query = """
    INSERT INTO reference (name, path, genome_count, arm_selection, description, example)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    # app.logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    # app.logger.info(config["example"])
    print(config["example"])
    # app.logger.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    try:
        cursor.execute(query, (
            config["name"], config["path"], config["genome_count"], config["arm_selection"], config["description"],
            config["example"]))
        connection.commit()
        # app.logger.info(f"inserted reference: {query}")
        print(f"inserted reference: {query}")
    except mariadb.Error as exception:
        # app.logger.info(f"error inserting reference: {exception}")
        print(f"error inserting reference: {exception}")


def insert_query(connection, uid, reference, email, date):
    cursor = connection.cursor()

    query = """
    INSERT INTO query (uid, reference, email, date)
    VALUES (?, ?, ?, ?)
    """

    try:
        cursor.execute(query, (uid, reference, email, date))
        connection.commit()
        # app.logger.info(f"inserted query: {query}")
        print(f"inserted query: {query}")
    except mariadb.Error as exception:
        # app.logger.info(f"error inserting query: {exception}")
        print(f"error inserting query: {exception}")
