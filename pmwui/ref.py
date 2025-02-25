#!/usr/bin/env python
import mariadb
import yaml


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


def read_reference(path):
    return yaml.safe_load(open(path))


def main():
    reference_configs = read_reference("/usr/users/JIC_a5/goz24vof/cmd-queue/test_ref.yaml")

    db_connection = connect()

    if db_connection is not None:
        create_reference_table(db_connection)

        for config in reference_configs:
            insert_reference(db_connection, config)


if __name__ == '__main__':
    main()