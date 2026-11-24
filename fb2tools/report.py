"""Отчёты о проверке: сбор результатов и вывод в форматах text, csv, json."""
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from . import __version__
from .checker import Problem, diagnose_file, iter_fb2_files
from .fixer import is_fixable

FORMATS = ("text", "csv", "json")
CSV_COLUMNS = ["path", "status", "code", "message", "fixable"]


@dataclass
class FileReport:
    path: Path
    problems: list[Problem]
    fixable: bool = False   # fix --fix полностью исправит этот файл

    @property
    def ok(self) -> bool:
        return not self.problems


def scan(folder: Path) -> list[FileReport]:
    """Проверяет все .fb2 и .fb2.zip в папке."""
    reports = []
    for path in iter_fb2_files(folder):
        problems = diagnose_file(path)
        fixable = bool(problems) and is_fixable(path)
        reports.append(FileReport(path, problems, fixable))
    return reports


def _selected(reports: list[FileReport], include_ok: bool) -> list[FileReport]:
    return reports if include_ok else [r for r in reports if not r.ok]


def render_text(reports: list[FileReport], stream: TextIO) -> None:
    for r in reports:
        if r.ok:
            continue
        stream.write(f"{r.path}\n")
        for p in r.problems:
            stream.write(f"    - {p.message}\n")


def render_csv(reports: list[FileReport], stream: TextIO, include_ok: bool,
               lineterminator: str) -> None:
    """Одна строка на одну проблему; файл без проблем (при --all) это одна строка со status=ok."""
    writer = csv.writer(stream, lineterminator=lineterminator)
    writer.writerow(CSV_COLUMNS)
    for r in _selected(reports, include_ok):
        if r.ok:
            writer.writerow([r.path, "ok", "", "", ""])
            continue
        fixable = "yes" if r.fixable else "no"
        for p in r.problems:
            writer.writerow([r.path, "error", p.code, p.message, fixable])


def build_json(folder: Path, reports: list[FileReport], include_ok: bool) -> dict:
    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool_version": __version__,
        "folder": str(folder),
        "total": len(reports),
        "with_errors": sum(1 for r in reports if not r.ok),
        "files": [
            {
                "path": str(r.path),
                "ok": r.ok,
                "fixable": r.fixable,
                "problems": [{"code": p.code, "message": p.message} for p in r.problems],
            }
            for r in _selected(reports, include_ok)
        ],
    }


def render(fmt: str, folder: Path, reports: list[FileReport], stream: TextIO, *,
           include_ok: bool = False, to_file: bool = False) -> None:
    """Выводит отчёт в stream. to_file=True: запись в файл (иначе в консоль)."""
    if fmt == "csv":
        render_csv(reports, stream, include_ok, "\r\n" if to_file else "\n")
    elif fmt == "json":
        # в консоль выводим с экранированием кириллицы: так не ломается при перенаправлении
        json.dump(build_json(folder, reports, include_ok), stream,
                  ensure_ascii=not to_file, indent=2)
        stream.write("\n")
    else:
        render_text(reports, stream)
