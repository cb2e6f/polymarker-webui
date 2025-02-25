#!/usr/bin/env python
import sys

import db


def submit(cmd):
    db.submit(cmd)


def main():
    if len(sys.argv) < 2:
        print("Usage: submit.py <cmd>")
        return
    submit(sys.argv[1])


if __name__ == "__main__":
    main()