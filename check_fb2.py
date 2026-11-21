#!/usr/bin/env python3
"""Проверка FB2-файлов: python3 check_fb2.py /путь/к/папке"""
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://www.gribuser.ru/xml/fictionbook/2.0"
XLINK = "http://www.w3.org/1999/xlink"


def check(data: bytes) -> list[str]:
    errors = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return [f"XML не разбирается: {e}"]

    if root.tag != f"{{{NS}}}FictionBook":
        return [f"неверный корневой элемент: {root.tag}"]

    if root.find(f"{{{NS}}}description") is None:
        errors.append("нет <description>")
    elif root.find(f"{{{NS}}}description/{{{NS}}}title-info") is None:
        errors.append("нет <title-info>")
    elif root.find(f"{{{NS}}}description/{{{NS}}}title-info/{{{NS}}}book-title") is None:
        errors.append("нет <book-title>")

    if root.find(f"{{{NS}}}body") is None:
        errors.append("нет <body>")

    # ссылки на картинки без соответствующих <binary>
    binaries = {b.get("id") for b in root.findall(f"{{{NS}}}binary")}
    for el in root.iter():
        href = el.get(f"{{{XLINK}}}href") or el.get("href")
        if href and href.startswith("#") and el.tag.endswith("image"):
            if href[1:] not in binaries:
                errors.append(f"картинка {href} не найдена среди <binary>")
    return errors


def main():
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bad = total = 0
    for p in sorted(folder.rglob("*")):
        name = p.name.lower()
        if not p.is_file() or not (name.endswith(".fb2") or name.endswith(".fb2.zip")):
            continue
        total += 1
        try:
            if name.endswith(".zip"):
                with zipfile.ZipFile(p) as z:
                    fb2 = [n for n in z.namelist() if n.lower().endswith(".fb2")]
                    if not fb2:
                        errs = ["в архиве нет .fb2"]
                    else:
                        errs = check(z.read(fb2[0]))
            else:
                errs = check(p.read_bytes())
        except Exception as e:
            errs = [f"ошибка чтения: {e}"]
        if errs:
            bad += 1
            print(f"{p}")
            for e in errs:
                print(f"    - {e}")
    print(f"\nПроверено: {total}, с ошибками: {bad}", file=sys.stderr)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
