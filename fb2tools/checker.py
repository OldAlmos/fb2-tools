"""Проверка структуры FB2-файлов."""
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterator
from pathlib import Path

NS = "http://www.gribuser.ru/xml/fictionbook/2.0"
XLINK = "http://www.w3.org/1999/xlink"


def check_bytes(data: bytes) -> list[str]:
    """Проверяет содержимое FB2, возвращает список ошибок (пустой, если всё хорошо)."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return [f"XML не разбирается: {e}"]

    if root.tag != f"{{{NS}}}FictionBook":
        return [f"неверный корневой элемент: {root.tag}"]

    errors = []
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


def iter_fb2_files(folder: Path) -> Iterator[Path]:
    """Рекурсивно перебирает .fb2 и .fb2.zip в папке."""
    for p in sorted(folder.rglob("*")):
        name = p.name.lower()
        if p.is_file() and (name.endswith(".fb2") or name.endswith(".fb2.zip")):
            yield p


def check_file(path: Path) -> list[str]:
    """Проверяет один файл (.fb2 или .fb2.zip), возвращает список ошибок."""
    try:
        if path.name.lower().endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                fb2 = [n for n in z.namelist() if n.lower().endswith(".fb2")]
                if not fb2:
                    return ["в архиве нет .fb2"]
                return check_bytes(z.read(fb2[0]))
        return check_bytes(path.read_bytes())
    except Exception as e:  # noqa: BLE001 - любая ошибка чтения это тоже результат проверки
        return [f"ошибка чтения: {e}"]
