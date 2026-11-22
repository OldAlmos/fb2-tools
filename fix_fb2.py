#!/usr/bin/env python3
"""Совместимость: python3 fix_fb2.py ПАПКА [--fix]  (то же, что fb2tools fix ПАПКА [--fix])."""
import sys

from fb2tools.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["fix", *sys.argv[1:]]))
