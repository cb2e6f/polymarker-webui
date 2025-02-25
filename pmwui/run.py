#!/usr/bin/env python
import threading
from time import sleep

import db


def worker(cv, s):
    while True:
        work = db.get(s)
        if work is not None:
            sleep(3)
            print(work)
            db.update(work[0], "DONE")
        else:
            print("...")
            cv.wait()



def main():

    e = threading.Event()
    s = threading.Semaphore()

    worker1 = threading.Thread(target=worker, args=(e, s))
    worker1.start()

    worker2 = threading.Thread(target=worker, args=(e, s))
    worker2.start()

    sleep(10)

    db.submit("t91")
    db.submit("t92")
    db.submit("t93")

    e.set()
    e.clear()
    worker1.join()
    worker2.join()


if __name__ == '__main__':
    main()