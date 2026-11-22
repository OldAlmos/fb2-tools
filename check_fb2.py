#!/usr/bin/env python3
"""Совместимость: python3 check_fb2.py ПАПКА  (то же, что fb2tools check ПАПКА)."""
import sys

from fb2tools.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["check", *sys.argv[1:]]))
