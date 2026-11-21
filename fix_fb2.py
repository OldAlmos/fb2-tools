#!/usr/bin/env python3
"""Починка FB2: python3 fix_fb2.py ПАПКА [--fix]"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# 1. Обрезанный корневой тег: любой незакрытый <FictionBook ... перед следующим <
HEAD = re.compile(rb'<FictionBook\b[^<>]*(?=<)')
ROOT = (b'<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" '
        b'xmlns:l="http://www.w3.org/1999/xlink">')

# 2. Мусор сразу после </description>: on>on>on>
TAIL = re.compile(rb'(</description>)[^<]*[^<\s][^<]*(?=<)')


def repair(data: bytes):
    notes = []
    data, n = HEAD.subn(lambda m: ROOT, data)
    if n:
        notes.append("обрезанный тег <FictionBook>")
    data, n = TAIL.subn(rb'\1', data)
    if n:
        notes.append("мусор после </description>")
    return data, notes


def parses(data: bytes) -> bool:
    try:
        ET.fromstring(data)
        return True
    except ET.ParseError:
        return False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fix = "--fix" in sys.argv
    folder = Path(args[0] if args else ".")

    found = fixed = unresolved = 0
    for p in sorted(folder.rglob("*")):
        if not p.is_file() or p.suffix.lower() != ".fb2":
            continue
        data = p.read_bytes()
        new, notes = repair(data)
        if not notes:
            continue
        found += 1
        print(f"{p}: {', '.join(notes)}")

        if not parses(new):
            unresolved += 1
            print("    ! после правки XML всё ещё не разбирается, файл не тронут")
            continue

        if fix:
            p.with_name(p.name + ".bak").write_bytes(data)
            p.write_bytes(new)
            fixed += 1

    print(f"\nНайдено: {found}, исправлено: {fixed}, "
          f"не удалось исправить: {unresolved}"
          + ("" if fix else " (пробный запуск, добавьте --fix)"))


if __name__ == "__main__":
    main()
