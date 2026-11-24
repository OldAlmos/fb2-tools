"""Починка известных повреждений FB2-файлов."""
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .checker import diagnose_bytes

# 1. Обрезанный корневой тег: любой незакрытый <FictionBook ... перед следующим <
HEAD = re.compile(rb'<FictionBook\b[^<>]*(?=<)')
ROOT = (b'<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" '
        b'xmlns:l="http://www.w3.org/1999/xlink">')

# 2. Мусор сразу после </description>: on>on>on>
TAIL = re.compile(rb'(</description>)[^<]*[^<\s][^<]*(?=<)')


@dataclass
class FixResult:
    path: Path
    notes: list[str] = field(default_factory=list)
    resolved: bool = False   # XML после правки разбирается
    written: bool = False    # файл реально перезаписан


def repair(data: bytes) -> tuple[bytes, list[str]]:
    """Применяет правила починки, возвращает (новые данные, список найденных проблем)."""
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


def is_fixable(path: Path) -> bool:
    """True, если fix полностью исправит файл: после правки проверка не находит проблем."""
    if path.suffix.lower() != ".fb2":
        return False
    try:
        data = path.read_bytes()
    except OSError:
        return False
    new, notes = repair(data)
    return bool(notes) and not diagnose_bytes(new)


def process_file(path: Path, apply: bool = False) -> FixResult | None:
    """Проверяет файл и при apply=True чинит его (с копией .bak).

    Возвращает None, если известных проблем в файле нет.
    """
    data = path.read_bytes()
    new, notes = repair(data)
    if not notes:
        return None

    result = FixResult(path=path, notes=notes, resolved=parses(new))
    if apply and result.resolved:
        path.with_name(path.name + ".bak").write_bytes(data)
        path.write_bytes(new)
        result.written = True
    return result
