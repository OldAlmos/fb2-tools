"""Удаление резервных копий *.fb2.bak, которые создаёт fb2tools fix."""
from collections.abc import Iterable, Iterator
from pathlib import Path


def iter_bak_files(folder: Path) -> Iterator[Path]:
    """Рекурсивно перебирает файлы *.fb2.bak (регистр не важен)."""
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.name.lower().endswith(".fb2.bak"):
            yield p


def delete_files(files: Iterable[Path]) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Удаляет файлы. Возвращает (удалённые, [(файл, причина ошибки)])."""
    deleted: list[Path] = []
    failed: list[tuple[Path, str]] = []
    for p in files:
        try:
            p.unlink()
            deleted.append(p)
        except OSError as e:
            failed.append((p, str(e)))
    return deleted, failed
