import mariadb


def open_db():
    db = mariadb.connect(
        host="localhost",
        user="re",
        password="",
        database="cmd_queue_db"
    )

    return db


def close_db(db):
    db.close()


def init_db():

    db = open_db()
    cursor = db.cursor()
    cursor.execute(
        "CREATE TABLE cmd_queue(id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL, cmd TEXT NOT NULL, status TEXT NOT NULL)")
    db.commit()

    cursor.close()
    db.close()