#!/usr/bin/env python3
"""Entrypoint: copy the entry image beside this file to /output/entry.png.

Standard library only, no network, deterministic: the same bytes every run.
The grader sets MAKEFUN_OUTPUT_DIR; without it, /output is used.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(HERE, "entry.png")
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(src, dst)


if __name__ == "__main__":
    main()
