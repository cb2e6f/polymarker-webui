from time import sleep


import mariadb


def open_db():
    db = mariadb.connect(
        host="localhost",
        user="re",
        password="",
        database="polymarker_webui"
    )

    return db


def close_db(db):
    db.close()


def init_db():
    db = mariadb.connect(
        host="localhost",
        user="re",
        password="",
    )

    cursor = db.cursor()
    # cursor.execute("DROP DATABASE IF EXISTS polymarker_webui")
    # cursor.execute("CREATE DATABASE polymarker_webui")
    cursor.execute("USE polymarker_webui")
    cursor.execute(
        "CREATE TABLE cmd_queue(id INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL, cmd TEXT NOT NULL, status TEXT NOT NULL)")
    db.commit()

    cursor.close()
    db.close()


def submit(cmd):
    print("SUB")
    db = open_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO cmd_queue(cmd, status) VALUES (?, ?)", (cmd, "SUB"))
    db.commit()
    cursor.close()
    db.close()


def get(s):
    s.acquire(blocking=True)
    db = open_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM cmd_queue WHERE status=?", ("SUB",))
    result = cursor.fetchone()
    if result is not None:
        cursor.execute("UPDATE cmd_queue SET status=? WHERE id=?", ("GOT",result[0]))
        db.commit()
    cursor.close()
    db.close()
    s.release()
    return result


def update(cmd, status):
    db = open_db()
    cursor = db.cursor()
    cursor.execute("UPDATE cmd_queue SET status=? WHERE id=?", (status, cmd))
    db.commit()
    cursor.close()
    db.close()


def delete(cmd):
    db = open_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM cmd_queue WHERE id=?", (cmd,))
    db.commit()
    cursor.close()
    db.close()

def worker(cv, s):
    while True:
        work = get(s)
        if work is not None:
            sleep(3)
            print(work)
            update(work[0], "DONE")
        else:
            print("...")
            cv.wait()