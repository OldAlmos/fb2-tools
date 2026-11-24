"""Проверка структуры FB2-файлов."""
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

NS = "http://www.gribuser.ru/xml/fictionbook/2.0"
XLINK = "http://www.w3.org/1999/xlink"


@dataclass(frozen=True)
class Problem:
    """Найденная проблема: устойчивый код (для таблиц и программ) и текст для человека."""
    code: str
    message: str


def diagnose_bytes(data: bytes) -> list[Problem]:
    """Проверяет содержимое FB2, возвращает список проблем (пустой, если всё хорошо)."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return [Problem("xml_parse", f"XML не разбирается: {e}")]

    if root.tag != f"{{{NS}}}FictionBook":
        return [Problem("wrong_root", f"неверный корневой элемент: {root.tag}")]

    problems: list[Problem] = []
    # посторонний текст между элементами верхнего уровня (например, "on>on>on>")
    if (root.text or "").strip() or any((child.tail or "").strip() for child in root):
        problems.append(Problem("stray_text", "посторонний текст внутри <FictionBook>"))

    if root.find(f"{{{NS}}}description") is None:
        problems.append(Problem("no_description", "нет <description>"))
    elif root.find(f"{{{NS}}}description/{{{NS}}}title-info") is None:
        problems.append(Problem("no_title_info", "нет <title-info>"))
    elif root.find(f"{{{NS}}}description/{{{NS}}}title-info/{{{NS}}}book-title") is None:
        problems.append(Problem("no_book_title", "нет <book-title>"))

    if root.find(f"{{{NS}}}body") is None:
        problems.append(Problem("no_body", "нет <body>"))

    # ссылки на картинки без соответствующих <binary>
    binaries = {b.get("id") for b in root.findall(f"{{{NS}}}binary")}
    for el in root.iter():
        href = el.get(f"{{{XLINK}}}href") or el.get("href")
        if href and href.startswith("#") and el.tag.endswith("image"):
            if href[1:] not in binaries:
                problems.append(Problem(
                    "missing_binary", f"картинка {href} не найдена среди <binary>"))
    return problems


def diagnose_file(path: Path) -> list[Problem]:
    """Проверяет один файл (.fb2 или .fb2.zip), возвращает список проблем."""
    try:
        if path.name.lower().endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                fb2 = [n for n in z.namelist() if n.lower().endswith(".fb2")]
                if not fb2:
                    return [Problem("zip_no_fb2", "в архиве нет .fb2")]
                return diagnose_bytes(z.read(fb2[0]))
        return diagnose_bytes(path.read_bytes())
    except Exception as e:  # noqa: BLE001 - любая ошибка чтения это тоже результат проверки
        return [Problem("read_error", f"ошибка чтения: {e}")]


def check_bytes(data: bytes) -> list[str]:
    """То же, что diagnose_bytes, но только тексты сообщений."""
    return [p.message for p in diagnose_bytes(data)]


def check_file(path: Path) -> list[str]:
    """То же, что diagnose_file, но только тексты сообщений."""
    return [p.message for p in diagnose_file(path)]


def iter_fb2_files(folder: Path) -> Iterator[Path]:
    """Рекурсивно перебирает .fb2 и .fb2.zip в папке."""
    for p in sorted(folder.rglob("*")):
        name = p.name.lower()
        if p.is_file() and (name.endswith(".fb2") or name.endswith(".fb2.zip")):
            yield p
