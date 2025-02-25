#!/usr/bin/env python
import sys


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


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print('Usage: python post_process_masks.py <masks_file_path> <des_file_path>')
        sys.exit(1)

    file_path = sys.argv[1]
    des_file_path = sys.argv[2]

    post_process_masks(file_path, des_file_path)