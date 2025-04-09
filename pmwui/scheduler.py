import logging
import threading
from asyncio import sleep

from pmwui import db

logger = logging.getLogger('gunicorn.error')


class Scheduler:
    workers = []
    running = False
    event = threading.Event()
    sem = threading.Semaphore()

    work = None

    def __init__(self, work):
        self.work = work
        self.workers.append(threading.Thread(target=self.worker))

    def worker(self):
        while self.running:
            logger.info("worker running")
            job = self.get()
            if job is not None:
                sleep(3)
                logger.info("^^^^^^^^^^^^^^^^^^^^^^^^^^")
                logger.info(job)
                logger.info("^^^^^^^^^^^^^^^^^^^^^^^^^^")
                try:
                    self.work(job[1])
                except Exception as exception:
                    logger.info(exception)
                    # update_query_status(work[1], "E: " + str(exception))
                self.delete(job[0])
            else:
                logger.info("...")
                self.event.wait()

    def poke(self):
        self.event.set()
        self.event.clear()

    def start(self):
        self.running = True
        self.workers[0].start()
        self.poke()

    def stop(self):
        self.running = False
        self.poke()
        self.workers[0].join()

    def get(self):
        self.sem.acquire(blocking=True)
        dbc = db.open_db()
        cursor = dbc.cursor()
        cursor.execute("SELECT * FROM cmd_queue WHERE status=?", ("SUB",))
        result = cursor.fetchone()
        if result is not None:
            cursor.execute("UPDATE cmd_queue SET status=? WHERE id=?", ("GOT", result[0]))
            dbc.commit()
        cursor.close()
        dbc.close()
        self.sem.release()
        return result

    @staticmethod
    def submit(cmd):
        logger.info("SUB")
        dbc = db.open_db()
        cursor = dbc.cursor()
        cursor.execute("INSERT INTO cmd_queue(cmd, status) VALUES (?, ?)", (cmd, "SUB"))
        dbc.commit()
        cursor.close()
        dbc.close()

    @staticmethod
    def delete(cmd):
        dbc = db.open_db()
        cursor = dbc.cursor()
        cursor.execute("DELETE FROM cmd_queue WHERE id=?", (cmd,))
        dbc.commit()
        cursor.close()
        dbc.close()

    @staticmethod
    def update(cmd, status):
        dbc = db.open_db()
        cursor = dbc.cursor()
        cursor.execute("UPDATE cmd_queue SET status=? WHERE id=?", (status, cmd))
        dbc.commit()
        cursor.close()
        dbc.close()

    @staticmethod
    def count():
        dbc = db.open_db()
        cursor = dbc.cursor()
        cursor.execute("SELECT COUNT(*) FROM cmd_queue")
        qcount = cursor.fetchone()[0]
        cursor.close()
        dbc.close()
        return qcount
